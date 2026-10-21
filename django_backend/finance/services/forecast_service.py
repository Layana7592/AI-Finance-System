import warnings
from datetime import datetime

import numpy as np
import pandas as pd
from django.db.models import Sum
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import adfuller

from finance.models import Transaction
from .research_scope import research_transactions


# ============================================================
# 1. PREPARE MONTHLY TRANSACTION DATA
# ============================================================

def get_monthly_transaction_data():
    """
    Prepare monthly income and expense transaction amounts.

    Income:
        Deposit

    Expense:
        Withdrawal + Payment + Purchase

    Transfer transactions are excluded because the dataset
    does not contain enough information to determine direction.

    This is the *frozen Jan 2024–Dec 2025 research sample*, not an ongoing
    live banking forecast. Later presentation events cannot lengthen the
    historical period or alter reported model comparisons.
    """

    transactions = (
        research_transactions(Transaction.objects.all())
        .values("transaction_time", "transaction_type")
        .annotate(total_amount=Sum("amount"))
        .order_by("transaction_time")
    )

    if not transactions:
        return {
            "income": pd.Series(dtype=float),
            "expense": pd.Series(dtype=float),
        }

    df = pd.DataFrame(transactions)

    df["transaction_time"] = pd.to_datetime(
        df["transaction_time"]
    )

    # -----------------------------
    # INCOME
    # -----------------------------

    income_df = df[
        df["transaction_type"] == "Deposit"
    ]

    income = (
        income_df
        .set_index("transaction_time")["total_amount"]
        .resample("MS")
        .sum()
        .asfreq("MS", fill_value=0)
    )

    # -----------------------------
    # EXPENSE
    # -----------------------------

    expense_df = df[
        df["transaction_type"].isin(
            [
                "Withdrawal",
                "Payment",
                "Purchase",
            ]
        )
    ]

    expense = (
        expense_df
        .set_index("transaction_time")["total_amount"]
        .resample("MS")
        .sum()
        .asfreq("MS", fill_value=0)
    )

    # Both targets must refer to the same calendar months; zeros represent
    # months with no transactions of that type.
    if not income.empty and not expense.empty:
        calendar = pd.date_range(
            start=min(income.index.min(), expense.index.min()),
            end=max(income.index.max(), expense.index.max()),
            freq="MS",
        )
        income = income.reindex(calendar, fill_value=0)
        expense = expense.reindex(calendar, fill_value=0)

    return {
        "income": income.astype(float),
        "expense": expense.astype(float),
    }
# ============================================================
# 2. STATIONARITY CHECK
# ============================================================

def check_stationarity(series):
    """
    Augmented Dickey-Fuller test.
    """

    series = series.dropna()

    if len(series) < 8:
        return {
            "stationary": None,
            "adf_statistic": None,
            "p_value": None,
            "message": "Not enough observations for stationarity test."
        }

    try:
        result = adfuller(series)
    except (ValueError, TypeError, ZeroDivisionError):
        return {
            "stationary": None,
            "adf_statistic": None,
            "p_value": None,
            "message": "Stationarity test unavailable for this series.",
        }

    adf_statistic = float(result[0])
    p_value = float(result[1])

    return {
        "stationary": p_value < 0.05,
        "adf_statistic": adf_statistic,
        "p_value": p_value,
        "message": (
            "Series is stationary."
            if p_value < 0.05
            else "Series is not stationary; differencing is appropriate."
        ),
    }


# ============================================================
# 3. SEASONAL NAIVE FORECAST
# ============================================================

def seasonal_naive_forecast(train, steps, season_length=12):
    """
    Forecast using the value from the same month in the previous year.
    """

    if len(train) < season_length:
        return np.repeat(train.iloc[-1], steps)

    values = train.iloc[-season_length:].values

    repeats = int(np.ceil(steps / season_length))

    forecast = np.tile(values, repeats)[:steps]

    return forecast


# ============================================================
# 4. SARIMA FORECAST
# ============================================================

def sarima_forecast(train, steps):
    """
    Generate a SARIMA forecast.

    Uses SARIMA with 12-month seasonality when the available
    training history is sufficient. If the model cannot be
    fitted, the error is raised so the validation layer can
    record the failed window instead of crashing the application.
    """

    train = np.asarray(train, dtype=float)

    if len(train) < 13:
        raise ValueError(
            "SARIMA requires at least 13 monthly observations."
        )

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        model = SARIMAX(
            train,
            order=(1, 1, 1),
            seasonal_order=(1, 1, 1, 12),
            enforce_stationarity=False,
            enforce_invertibility=False,
        )

        fitted_model = model.fit(
            disp=False,
            maxiter=200,
        )

    forecast = fitted_model.forecast(steps=steps)

    return np.asarray(forecast, dtype=float)
# ============================================================
# 5. METRICS
# ============================================================

def calculate_metrics(actual, predicted):
    """
    Calculate MAE, RMSE and MAPE.
    """

    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)

    if (
        len(actual) == 0
        or len(actual) != len(predicted)
        or not np.all(np.isfinite(actual))
        or not np.all(np.isfinite(predicted))
    ):
        return {"mae": None, "rmse": None, "mape": None}

    mae = np.mean(np.abs(actual - predicted))

    rmse = np.sqrt(
        np.mean((actual - predicted) ** 2)
    )

    non_zero = actual != 0

    if np.any(non_zero):
        mape = (
            np.mean(
                np.abs(
                    (actual[non_zero] - predicted[non_zero])
                    / actual[non_zero]
                )
            )
            * 100
        )
    else:
        mape = None

    return {
        "mae": round(float(mae), 2),
        "rmse": round(float(rmse), 2),
        "mape": (
            round(float(mape), 2)
            if mape is not None
            else None
        ),
    }


# ============================================================
# 6. EXPANDING-WINDOW VALIDATION
# ============================================================

def _forecast_error_analysis(rows):
    """Explain the size, direction and timing of measured one-step errors."""
    if not rows:
        return {
            "observations": 0, "mean_signed_error": None,
            "median_absolute_error": None, "max_absolute_error": None,
            "worst_windows": [],
        }
    errors = np.asarray([row["predicted"] - row["actual"] for row in rows], dtype=float)
    absolute = np.abs(errors)
    worst = sorted(
        rows, key=lambda row: abs(row["predicted"] - row["actual"]), reverse=True
    )[:3]
    return {
        "observations": len(rows),
        "mean_signed_error": round(float(np.mean(errors)), 2),
        "median_absolute_error": round(float(np.median(absolute)), 2),
        "max_absolute_error": round(float(np.max(absolute)), 2),
        "worst_windows": worst,
    }


def expanding_window_validation(series, initial_train_size=12, horizon=1):
    """Expanding-window evaluation with legacy and STRICTLY PAIRED metrics.

    'seasonal_naive' retains all available baseline windows even when SARIMA
    diverges, preserving the original academic experiment and transparency.
    'paired' evaluates BOTH models only on the identical timestamps where
    SARIMA completed successfully; SARIMA failures are kept in the timeline.
    Every row is traceable to a validation month, with signed residuals
    calculated as predicted minus observed.
    """
    baseline_rows = []
    paired_baseline_rows = []
    sarima_rows = []
    failures = []
    all_windows = []
    if len(series) <= initial_train_size:
        empty = calculate_metrics([], [])
        return {
            "seasonal_naive": empty, "sarima": empty,
            "observations": 0, "sarima_observations": 0,
            "paired": {
                "seasonal_naive": empty, "sarima": empty,
                "observations": 0, "baseline_error_analysis": _forecast_error_analysis([]),
                "sarima_error_analysis": _forecast_error_analysis([]),
            },
            "validation_windows": [],
            "sarima_failures": [],
        }

    for end_index in range(initial_train_size, len(series), horizon):
        train = series.iloc[:end_index]
        test = series.iloc[end_index:end_index + horizon]
        if test.empty:
            break

        naive = np.asarray(
            seasonal_naive_forecast(train, len(test), season_length=12),
            dtype=float,
        )
        if len(naive) != len(test) or not np.all(np.isfinite(naive)):
            raise ValueError("Seasonal-Naive generated invalid validation values.")
        actual = np.asarray(test.values, dtype=float)
        dates = [
            value.date().isoformat() if hasattr(value, "date") else str(value)
            for value in test.index
        ]
        for date, observed, predicted in zip(dates, actual, naive):
            baseline_rows.append({
                "month": date, "actual": float(observed),
                "predicted": float(predicted),
            })

        sarima = None
        reason = None
        try:
            sarima = np.asarray(sarima_forecast(train, len(test)), dtype=float)
            if len(sarima) != len(test) or not np.all(np.isfinite(sarima)):
                reason = "non_finite_or_wrong_horizon"
        except Exception as exc:
            reason = type(exc).__name__

        if reason is not None:
            for date, observed, predicted in zip(dates, actual, naive):
                failures.append({"month": date, "reason": reason})
                all_windows.append({
                    "month": date, "observed": float(observed),
                    "seasonal_naive": float(predicted),
                    "sarima": None, "sarima_status": "failed",
                })
            continue

        for date, observed, nv, sv in zip(dates, actual, naive, sarima):
            paired_baseline_rows.append({
                "month": date, "actual": float(observed), "predicted": float(nv),
            })
            sarima_rows.append({
                "month": date, "actual": float(observed), "predicted": float(sv),
            })
            all_windows.append({
                "month": date, "observed": float(observed),
                "seasonal_naive": float(nv), "sarima": float(sv),
                "sarima_status": "success",
            })

    def metrics(rows):
        return calculate_metrics(
            [x["actual"] for x in rows], [x["predicted"] for x in rows]
        )

    return {
        "seasonal_naive": metrics(baseline_rows),
        "sarima": metrics(sarima_rows),
        "observations": len(baseline_rows),
        "sarima_observations": len(sarima_rows),
        "paired": {
            "seasonal_naive": metrics(paired_baseline_rows),
            "sarima": metrics(sarima_rows),
            "observations": len(sarima_rows),
            "baseline_error_analysis": _forecast_error_analysis(paired_baseline_rows),
            "sarima_error_analysis": _forecast_error_analysis(sarima_rows),
        },
        "validation_windows": all_windows,
        "sarima_failures": failures,
    }


# ============================================================
# 7. COMPLETE FORECASTING EVALUATION
# ============================================================

def evaluate_forecast_models():
    """
    Evaluate income and expense forecasting separately.

    Includes:
        - monthly income/expense data
        - stationarity test
        - expanding-window validation
        - Seasonal Naive
        - SARIMA
        - MAE
        - RMSE
        - MAPE
    """

    data = get_monthly_transaction_data()

    income = data["income"]
    expense = data["expense"]

    if income.empty or expense.empty:
        return {
            "status": "error",
            "message": "No transaction data available.",
        }

    income_stationarity = check_stationarity(income)
    expense_stationarity = check_stationarity(expense)

    income_validation = expanding_window_validation(
        income,
        initial_train_size=13,
        horizon=1,
    )

    expense_validation = expanding_window_validation(
        expense,
        initial_train_size=13,
        horizon=1,
    )

    return {
        "status": "success",

        "data_period": {
            "start": str(income.index.min().date()),
            "end": str(income.index.max().date()),
        },

        "number_of_months": len(income),

        "income": {
            "stationarity": income_stationarity,
            "validation": {
                "method": "Expanding-window one-step-ahead validation",
                "observations": income_validation["observations"],
                "sarima_observations": income_validation["sarima_observations"],
                "sarima_failures": income_validation["sarima_failures"],
                "windows": income_validation["validation_windows"],
                "paired_comparison": income_validation["paired"],
            },
            "models": {
                "seasonal_naive": income_validation["seasonal_naive"],
                "sarima": income_validation["sarima"],
            },
        },

        "expense": {
            "stationarity": expense_stationarity,
            "validation": {
                "method": "Expanding-window one-step-ahead validation",
                "observations": expense_validation["observations"],
                "sarima_observations": expense_validation["sarima_observations"],
                "sarima_failures": expense_validation["sarima_failures"],
                "windows": expense_validation["validation_windows"],
                "paired_comparison": expense_validation["paired"],
            },
            "models": {
                "seasonal_naive": expense_validation["seasonal_naive"],
                "sarima": expense_validation["sarima"],
            },
        },

        "sarima_configuration": {
            "order": "(1,1,1)",
            "seasonal_order": "(1,1,1,12)",
            "seasonality": "12 months",
        },
    }
# ============================================================
# 8. GENERATE FUTURE FORECAST
# ============================================================

def select_model(naive_mape, sarima_mape):
    """Choose the model with the lower valid MAPE."""
    if naive_mape is None or not np.isfinite(naive_mape):
        if sarima_mape is not None and np.isfinite(sarima_mape):
            return "sarima"
        return "seasonal_naive"
    if sarima_mape is None or not np.isfinite(sarima_mape):
        return "seasonal_naive"
    return "seasonal_naive" if naive_mape <= sarima_mape else "sarima"


def generate_series_forecast(series, months, selected_model):
    """Generate a forecast with Seasonal Naive fallback."""
    if selected_model == "sarima":
        try:
            forecast = np.asarray(sarima_forecast(series, months), dtype=float)
            if len(forecast) == months and np.all(np.isfinite(forecast)):
                return np.maximum(forecast, 0), "sarima"
        except Exception:
            pass

    forecast = np.asarray(
        seasonal_naive_forecast(series, months, season_length=12),
        dtype=float,
    )
    if len(forecast) != months or not np.all(np.isfinite(forecast)):
        raise ValueError("Seasonal Naive produced an invalid forecast.")
    return np.maximum(forecast, 0), "seasonal_naive"


def generate_forecast(months=12):
    """Choose a validated method per series, falling back to Seasonal-Naive.

    Model selection uses MAPE where defined. SARIMA is eligible only if all
    baseline validation windows also produced finite SARIMA predictions; a
    partial comparison cannot justify selecting the more complex model.
    """
    if type(months) is not int or not 1 <= months <= 24:
        raise ValueError("Forecast horizon must be an integer from 1 to 24.")

    data = get_monthly_transaction_data()
    income = data["income"]
    expense = data["expense"]
    if income.empty or expense.empty:
        return []

    income_validation = expanding_window_validation(
        income, initial_train_size=13, horizon=1
    )
    expense_validation = expanding_window_validation(
        expense, initial_train_size=13, horizon=1
    )

    def choose(validation):
        naive_mape = validation["seasonal_naive"]["mape"]
        sarima_mape = validation["sarima"]["mape"]
        if validation["sarima_observations"] < validation["observations"]:
            sarima_mape = None
        return select_model(naive_mape, sarima_mape)

    income_forecast, _income_method = generate_series_forecast(
        income, months, choose(income_validation)
    )
    expense_forecast, _expense_method = generate_series_forecast(
        expense, months, choose(expense_validation)
    )

    # Never expose invalid values to the persistence layer.
    if not np.all(np.isfinite(income_forecast)) or not np.all(np.isfinite(expense_forecast)):
        raise ValueError("Forecast returned non-finite values.")

    last_date = income.index[-1]  # Income/expense now share one calendar.
    return [
        {
            "forecast_month": (last_date + pd.DateOffset(months=i)).date(),
            "predicted_income": round(float(income_forecast[i - 1]), 2),
            "predicted_expense": round(float(expense_forecast[i - 1]), 2),
        }
        for i in range(1, months + 1)
    ]
