import warnings
from datetime import datetime

import numpy as np
import pandas as pd
from django.db.models import Sum
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import adfuller

from finance.models import Transaction


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
    """

    transactions = (
        Transaction.objects
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

    result = adfuller(series)

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

def expanding_window_validation(
    series,
    initial_train_size=12,
    horizon=1,
):
    """
    Expanding-window one-step-ahead validation.

    Example:

    Train: Jan-Dec
    Predict: Jan

    Train: Jan-Jan
    Predict: Feb

    Train: Jan-Feb
    Predict: Mar

    ...
    """

    actual_values = []
    seasonal_predictions = []
    sarima_predictions = []

    total_points = len(series)

    if total_points <= initial_train_size:
        return {
            "seasonal_naive": calculate_metrics([], []),
            "sarima": calculate_metrics([], []),
            "observations": 0,
        }

    for end_index in range(
        initial_train_size,
        total_points,
        horizon,
    ):

        train = series.iloc[:end_index]

        test = series.iloc[
            end_index:end_index + horizon
        ]

        if len(test) == 0:
            break

        # ----------------------------
        # Seasonal Naive
        # ----------------------------

        seasonal_prediction = seasonal_naive_forecast(
            train,
            len(test),
            season_length=12,
        )

        # ----------------------------
        # SARIMA
        # ----------------------------

        try:
            sarima_prediction = sarima_forecast(
                train,
                len(test),
            )
        except Exception:
            # If SARIMA cannot fit a particular
            # expanding window, skip that window.
            continue

        actual_values.extend(test.values)

        seasonal_predictions.extend(
            seasonal_prediction
        )

        sarima_predictions.extend(
            sarima_prediction
        )

    return {
        "seasonal_naive": calculate_metrics(
            actual_values,
            seasonal_predictions,
        ),
        "sarima": calculate_metrics(
            actual_values,
            sarima_predictions,
        ),
        "observations": len(actual_values),
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

def generate_forecast(months=12):
    """
    Generate future income and expense forecasts.

    Uses the forecasting model selected through validation.
    """

    data = get_monthly_transaction_data()

    income = data["income"]
    expense = data["expense"]

    if income.empty or expense.empty:
        return []

    # --------------------------------------------------
    # INCOME FORECAST
    # --------------------------------------------------

    income_forecast = seasonal_naive_forecast(
        income,
        months,
        season_length=12,
    )

    # --------------------------------------------------
    # EXPENSE FORECAST
    # --------------------------------------------------

    expense_forecast = seasonal_naive_forecast(
        expense,
        months,
        season_length=12,
    )

    income_forecast = np.maximum(
        income_forecast,
        0,
    )

    expense_forecast = np.maximum(
        expense_forecast,
        0,
    )

    # --------------------------------------------------
    # BUILD RESULTS
    # --------------------------------------------------

    results = []

    last_date = income.index[-1]

    for i in range(1, months + 1):

        forecast_date = (
            last_date
            + pd.DateOffset(months=i)
        )

        results.append({
            "forecast_month": forecast_date.date(),
            "predicted_income": round(
                float(income_forecast[i - 1]),
                2,
            ),
            "predicted_expense": round(
                float(expense_forecast[i - 1]),
                2,
            ),
        })

    return results