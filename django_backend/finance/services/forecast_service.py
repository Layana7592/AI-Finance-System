from decimal import Decimal

import numpy as np
import pandas as pd
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import adfuller

from finance.models import Transaction, FinancialForecast


# ============================================================
# GET MONTHLY DATA
# ============================================================

def get_monthly_data():
    """
    Get monthly income and expense totals.

    Income:
        Deposit

    Expenses:
        Withdrawal, Payment, Purchase

    Transfers are ignored because they are internal movements.
    """

    transactions = (
        Transaction.objects
        .annotate(month=TruncMonth("transaction_time"))
        .values("month", "transaction_type")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )

    data = {}

    for row in transactions:
        month = row["month"]

        if month not in data:
            data[month] = {
                "income": Decimal("0.00"),
                "expense": Decimal("0.00"),
            }

        transaction_type = str(
            row["transaction_type"]
        ).lower()

        total = row["total"] or Decimal("0.00")

        if transaction_type == "deposit":
            data[month]["income"] += total

        elif transaction_type in [
            "withdrawal",
            "payment",
            "purchase",
        ]:
            data[month]["expense"] += total

    return data


# ============================================================
# STATIONARITY CHECK
# ============================================================

def check_stationarity(series):
    """
    Check stationarity using the Augmented Dickey-Fuller test.

    H0:
        The series has a unit root and is non-stationary.

    p-value < 0.05:
        Evidence against non-stationarity.

    p-value >= 0.05:
        Non-stationarity cannot be ruled out.
    """

    series = pd.Series(
        series,
        dtype="float64"
    ).dropna().reset_index(drop=True)

    if len(series) < 8:
        return {
            "test": "Augmented Dickey-Fuller",
            "statistic": None,
            "p_value": None,
            "stationary": None,
            "interpretation": (
                "Not enough observations for a reliable "
                "stationarity test."
            ),
        }

    if series.nunique() <= 1:
        return {
            "test": "Augmented Dickey-Fuller",
            "statistic": None,
            "p_value": None,
            "stationary": None,
            "interpretation": (
                "The series is constant, so the ADF test "
                "is not applicable."
            ),
        }

    try:
        statistic, p_value, _, _, _, _ = adfuller(
            series,
            autolag="AIC",
        )

        stationary = bool(p_value < 0.05)

        if stationary:
            interpretation = (
                "The ADF test rejects the unit-root null "
                "hypothesis at the 5% level; the series "
                "appears stationary."
            )
        else:
            interpretation = (
                "The ADF test does not reject the unit-root "
                "null hypothesis at the 5% level; "
                "non-stationarity may be present."
            )

        return {
            "test": "Augmented Dickey-Fuller",
            "statistic": round(float(statistic), 4),
            "p_value": round(float(p_value), 4),
            "stationary": stationary,
            "interpretation": interpretation,
        }

    except Exception as exc:
        return {
            "test": "Augmented Dickey-Fuller",
            "statistic": None,
            "p_value": None,
            "stationary": None,
            "interpretation": (
                f"Stationarity test failed: {str(exc)}"
            ),
        }


# ============================================================
# SEASONALITY CHECK
# ============================================================

def check_seasonality(
    series,
    seasonal_period=12,
):
    """
    Inspect yearly seasonality using lag-12 autocorrelation.

    For monthly financial data:
        seasonal_period = 12

    A stronger positive lag-12 correlation indicates that
    values tend to resemble the same month in the previous year.

    This is a diagnostic, not proof of seasonality.
    """

    series = pd.Series(
        series,
        dtype="float64"
    ).dropna().reset_index(drop=True)

    if len(series) <= seasonal_period:
        return {
            "seasonal_period": seasonal_period,
            "lag_correlation": None,
            "seasonality_detected": None,
            "interpretation": (
                "Not enough observations to inspect "
                "lag-12 seasonality."
            ),
        }

    try:
        correlation = series.autocorr(
            lag=seasonal_period
        )

        if pd.isna(correlation):
            return {
                "seasonal_period": seasonal_period,
                "lag_correlation": None,
                "seasonality_detected": None,
                "interpretation": (
                    "Lag-12 correlation could not be calculated."
                ),
            }

        correlation = float(correlation)

        # Diagnostic threshold only; it is not a statistical
        # significance test.
        seasonality_detected = bool(
            correlation >= 0.50
        )

        if seasonality_detected:
            interpretation = (
                "The series shows a noticeable lag-12 "
                "relationship, supporting yearly seasonality."
            )
        else:
            interpretation = (
                "The lag-12 relationship is weak or moderate; "
                "strong yearly seasonality is not clearly established."
            )

        return {
            "seasonal_period": seasonal_period,
            "lag_correlation": round(correlation, 4),
            "seasonality_detected": seasonality_detected,
            "interpretation": interpretation,
        }

    except Exception as exc:
        return {
            "seasonal_period": seasonal_period,
            "lag_correlation": None,
            "seasonality_detected": None,
            "interpretation": (
                f"Seasonality check failed: {str(exc)}"
            ),
        }


# ============================================================
# SEASONAL-NAIVE FORECAST
# ============================================================

def seasonal_naive_forecast(
    train_series,
    periods=12,
    seasonal_period=12,
):
    """
    Seasonal-naive forecasting.

    Each future value is predicted using the value from
    the same month in the previous year.

    Example:
        Jan 2025 -> Jan 2024
        Feb 2025 -> Feb 2024
        ...
        Dec 2025 -> Dec 2024

    This is the baseline model used for comparison
    against SARIMA.
    """

    series = pd.Series(
        train_series,
        dtype="float64",
    ).reset_index(drop=True)

    if len(series) < seasonal_period:
        raise ValueError(
            "At least 12 months of training data "
            "is required for seasonal-naive forecasting."
        )

    predictions = []

    for i in range(periods):
        value = float(
            series.iloc[
                len(series)
                - seasonal_period
                + (i % seasonal_period)
            ]
        )

        predictions.append(
            max(0.0, value)
        )

    return predictions


# ============================================================
# SARIMA FORECAST
# ============================================================

def sarima_forecast(
    train_series,
    periods=12,
):
    """
    Forecast using a stationarity-aware SARIMA/ARIMA model.

    For short training windows, seasonal AR parameters are not
    estimated because there are not enough observations.

    If SARIMA fitting fails, Seasonal-Naive is used as fallback.
    """

    series = pd.Series(
        train_series,
        dtype="float64",
    ).reset_index(drop=True)

    if len(series) == 0:
        return [0.0] * periods

    if len(series) < 12:
        mean_value = float(series.mean())

        return [
            max(0.0, mean_value)
            for _ in range(periods)
        ]

    stationarity = check_stationarity(series)

    d_order = 0 if stationarity["stationary"] else 1

    try:
        # --------------------------------------------------
        # SHORT SERIES
        # --------------------------------------------------
        # With fewer than 24 observations, do not estimate
        # seasonal AR parameters.
        # --------------------------------------------------

        if len(series) < 24:

            model = SARIMAX(
                series,
                order=(1, d_order, 0),
                seasonal_order=(0, 0, 0, 0),
                trend="n" if d_order == 1 else "c",
                enforce_stationarity=False,
                enforce_invertibility=False,
            )

        # --------------------------------------------------
        # LONGER SERIES
        # --------------------------------------------------
        # Only estimate seasonal structure when at least
        # two complete seasonal cycles are available.
        # --------------------------------------------------

        else:

            model = SARIMAX(
                series,
                order=(1, d_order, 0),
                seasonal_order=(1, 0, 0, 12),
                trend="n" if d_order == 1 else "c",
                enforce_stationarity=False,
                enforce_invertibility=False,
            )

        fitted_model = model.fit(
            disp=False,
        )

        raw_forecast = fitted_model.forecast(
            steps=periods
        )

        result = []

        for value in raw_forecast:

            value = float(value)

            if pd.isna(value):
                value = float(
                    series.iloc[-12:].mean()
                )

            result.append(
                max(0.0, value)
            )

        return result

    except Exception:

        return seasonal_naive_forecast(
            series,
            periods=periods,
            seasonal_period=12,
        )
# ============================================================
# FORECAST METRICS
# ============================================================

def calculate_forecast_metrics(
    actual,
    predicted,
):
    """
    Calculate standard forecasting metrics.

    Metrics:
        MAE
        RMSE
        MAPE

    Lower values indicate better performance.
    """

    actual = np.asarray(
        actual,
        dtype=float,
    )

    predicted = np.asarray(
        predicted,
        dtype=float,
    )

    if len(actual) != len(predicted):
        raise ValueError(
            "Actual and predicted values "
            "must have the same length."
        )

    errors = actual - predicted

    mae = float(
        np.mean(
            np.abs(errors)
        )
    )

    rmse = float(
        np.sqrt(
            np.mean(
                errors ** 2
            )
        )
    )

    # MAPE is calculated only for non-zero
    # actual values.
    non_zero = actual != 0

    if np.any(non_zero):
        mape = float(
            np.mean(
                np.abs(
                    (
                        actual[non_zero]
                        - predicted[non_zero]
                    )
                    / actual[non_zero]
                )
            )
            * 100
        )
    else:
        mape = 0.0

    return {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "mape": round(mape, 2),
    }


# ============================================================
# EXPANDING-WINDOW MODEL VALIDATION
# ============================================================

def evaluate_series_models(
    series,
    train_periods=12,
    validation_periods=12,
):
    """
    Compare Seasonal-Naive and SARIMA using expanding-window
    one-step-ahead validation.

    Example with 24 months:

        Fold 1:
            Train = months 1-12
            Test  = month 13

        Fold 2:
            Train = months 1-13
            Test  = month 14

        ...

        Fold 12:
            Train = months 1-23
            Test  = month 24

    This is stronger than using only one fixed
    train/validation split because the model is
    repeatedly evaluated at different points in time.

    The validation is chronological. No random shuffling
    is used.
    """

    series = pd.Series(
        series,
        dtype="float64",
    ).reset_index(drop=True)

    required_length = (
        train_periods
        + validation_periods
    )

    if len(series) < required_length:
        raise ValueError(
            f"At least {required_length} months "
            "are required for expanding-window validation."
        )

    # --------------------------------------------------------
    # DIAGNOSTICS ON THE COMPLETE SERIES
    # --------------------------------------------------------

    stationarity = check_stationarity(
        series
    )

    seasonality = check_seasonality(
        series,
        seasonal_period=12,
    )

    # --------------------------------------------------------
    # EXPANDING-WINDOW VALIDATION
    # --------------------------------------------------------

    seasonal_naive_actual = []
    seasonal_naive_predictions = []

    sarima_actual = []
    sarima_predictions = []

    fold_results = []

    for fold in range(validation_periods):

        train_end = (
            train_periods
            + fold
        )

        train = series.iloc[
            :train_end
        ]

        actual_value = float(
            series.iloc[train_end]
        )

        # ----------------------------------------------------
        # SEASONAL-NAIVE ONE-STEP FORECAST
        # ----------------------------------------------------

        seasonal_prediction = float(
            seasonal_naive_forecast(
                train,
                periods=1,
                seasonal_period=12,
            )[0]
        )

        # ----------------------------------------------------
        # SARIMA ONE-STEP FORECAST
        # ----------------------------------------------------

        sarima_prediction = float(
            sarima_forecast(
                train,
                periods=1,
            )[0]
        )

        seasonal_naive_actual.append(
            actual_value
        )

        seasonal_naive_predictions.append(
            seasonal_prediction
        )

        sarima_actual.append(
            actual_value
        )

        sarima_predictions.append(
            sarima_prediction
        )

        fold_results.append(
            {
                "fold": fold + 1,
                "training_months": len(train),
                "actual": round(
                    actual_value,
                    2,
                ),
                "seasonal_naive_prediction": round(
                    seasonal_prediction,
                    2,
                ),
                "sarima_prediction": round(
                    sarima_prediction,
                    2,
                ),
            }
        )

    # --------------------------------------------------------
    # MODEL METRICS
    # --------------------------------------------------------

    seasonal_naive_metrics = (
        calculate_forecast_metrics(
            seasonal_naive_actual,
            seasonal_naive_predictions,
        )
    )

    sarima_metrics = (
        calculate_forecast_metrics(
            sarima_actual,
            sarima_predictions,
        )
    )

    # --------------------------------------------------------
    # MAE STABILITY
    # --------------------------------------------------------

    seasonal_naive_errors = np.abs(
        np.asarray(
            seasonal_naive_actual,
            dtype=float,
        )
        - np.asarray(
            seasonal_naive_predictions,
            dtype=float,
        )
    )

    sarima_errors = np.abs(
        np.asarray(
            sarima_actual,
            dtype=float,
        )
        - np.asarray(
            sarima_predictions,
            dtype=float,
        )
    )

    seasonal_naive_mae_std = float(
        np.std(
            seasonal_naive_errors
        )
    )

    sarima_mae_std = float(
        np.std(
            sarima_errors
        )
    )

    seasonal_naive_metrics[
        "mae_std"
    ] = round(
        seasonal_naive_mae_std,
        2,
    )

    sarima_metrics[
        "mae_std"
    ] = round(
        sarima_mae_std,
        2,
    )

    # --------------------------------------------------------
    # DETERMINE BETTER MODEL
    # --------------------------------------------------------

    # MAE is the primary model-selection metric.
    if (
        sarima_metrics["mae"]
        < seasonal_naive_metrics["mae"]
    ):
        best_model = "SARIMA"

    elif (
        seasonal_naive_metrics["mae"]
        < sarima_metrics["mae"]
    ):
        best_model = "Seasonal-Naive"

    else:
        best_model = "Equal"

    # --------------------------------------------------------
    # RETURN RESULTS
    # --------------------------------------------------------

    return {
        "diagnostics": {
            "stationarity": stationarity,
            "seasonality": seasonality,
        },
        "validation": {
            "method": "Expanding-window one-step-ahead validation",
            "initial_training_months": train_periods,
            "validation_months": validation_periods,
            "folds": validation_periods,
        },
        "seasonal_naive": {
            **seasonal_naive_metrics,
            "predictions": [
                round(value, 2)
                for value
                in seasonal_naive_predictions
            ],
        },
        "sarima": {
            **sarima_metrics,
            "predictions": [
                round(value, 2)
                for value
                in sarima_predictions
            ],
        },
        "actual": [
            round(value, 2)
            for value in seasonal_naive_actual
        ],
        "fold_results": fold_results,
        "best_model": best_model,
    }


# ============================================================
# COMPLETE FORECAST MODEL EVALUATION
# ============================================================

def evaluate_forecast_models():
    """
    Compare Seasonal-Naive and SARIMA for:

        1. Income
        2. Expense

    Evaluation includes:

        - ADF stationarity test
        - Lag-12 seasonality diagnostic
        - Expanding-window validation
        - MAE
        - RMSE
        - MAPE
        - MAE standard deviation
    """

    monthly_data = get_monthly_data()

    if len(monthly_data) < 24:
        raise ValueError(
            "At least 24 months of historical "
            "transaction data are required."
        )

    months = sorted(
        monthly_data.keys()
    )

    income_values = [
        float(
            monthly_data[month]["income"]
        )
        for month in months
    ]

    expense_values = [
        float(
            monthly_data[month]["expense"]
        )
        for month in months
    ]

    # --------------------------------------------------------
    # EVALUATE INCOME
    # --------------------------------------------------------

    income_results = evaluate_series_models(
        income_values,
        train_periods=12,
        validation_periods=12,
    )

    # --------------------------------------------------------
    # EVALUATE EXPENSE
    # --------------------------------------------------------

    expense_results = evaluate_series_models(
        expense_values,
        train_periods=12,
        validation_periods=12,
    )

    return {
        "dataset": {
            "months": len(months),
            "training_months": 12,
            "validation_months": 12,
            "validation_method": (
                "Expanding-window one-step-ahead validation"
            ),
            "training_start": str(
                months[0]
            ),
            "training_end": str(
                months[11]
            ),
            "validation_start": str(
                months[12]
            ),
            "validation_end": str(
                months[23]
            ),
        },
        "income": income_results,
        "expense": expense_results,
    }


# ============================================================
# PRODUCTION FORECAST SERIES
# ============================================================

def forecast_series(
    series,
    periods=12,
):
    """
    Generate production forecasts.

    Uses the same SARIMA model as the evaluation.

    Safety limits are applied so forecasts do not
    become unrealistically large or negative.

    If SARIMA fails, Seasonal-Naive is used.
    """

    series = pd.Series(
        series,
        dtype="float64",
    ).reset_index(drop=True)

    if len(series) == 0:
        return [0.0] * periods

    if len(series) < 12:
        mean_value = float(
            series.mean()
        )

        return [
            max(0.0, mean_value)
            for _ in range(periods)
        ]

    # --------------------------------------------------------
    # HISTORICAL REFERENCE VALUES
    # --------------------------------------------------------

    last_12 = series.iloc[-12:]

    historical_mean = float(
        last_12.mean()
    )

    historical_min = float(
        last_12.min()
    )

    historical_max = float(
        last_12.max()
    )

    # --------------------------------------------------------
    # SARIMA
    # --------------------------------------------------------

    try:
        model = SARIMAX(
            series,
            order=(1, 0, 0),
            seasonal_order=(0, 0, 0, 12),
            trend="c",
            enforce_stationarity=False,
            enforce_invertibility=False,
        )

        fitted_model = model.fit(
            disp=False
        )

        raw_forecast = fitted_model.forecast(
            steps=periods
        )

        result = []

        # ----------------------------------------------------
        # SAFETY BOUNDARIES
        # ----------------------------------------------------

        lower_limit = (
            historical_min * 0.70
        )

        upper_limit = (
            historical_max * 1.30
        )

        for value in raw_forecast:

            value = float(value)

            if pd.isna(value):
                value = historical_mean

            value = max(
                lower_limit,
                min(
                    value,
                    upper_limit,
                )
            )

            result.append(
                max(0.0, value)
            )

        return result

    except Exception:
        return seasonal_naive_forecast(
            series,
            periods=periods,
            seasonal_period=12,
        )


# ============================================================
# GENERATE PRODUCTION FORECAST
# ============================================================

def generate_forecast(
    periods=12,
):
    """
    Generate and save future monthly income
    and expense forecasts.

    The complete historical dataset is used.

    For the current dataset:

        Historical:
            Jan 2024 - Dec 2025

        Forecast:
            Jan 2026 - Dec 2026

    Returns exactly `periods` FinancialForecast objects.
    """

    if periods <= 0:
        raise ValueError(
            "Forecast periods must be greater than 0."
        )

    monthly_data = get_monthly_data()

    if len(monthly_data) < 12:
        raise ValueError(
            "At least 12 months of historical "
            "transaction data is required."
        )

    # --------------------------------------------------------
    # SORT MONTHS
    # --------------------------------------------------------

    months = sorted(
        monthly_data.keys()
    )

    # --------------------------------------------------------
    # INCOME
    # --------------------------------------------------------

    income_values = [
        float(
            monthly_data[month]["income"]
        )
        for month in months
    ]

    # --------------------------------------------------------
    # EXPENSE
    # --------------------------------------------------------

    expense_values = [
        float(
            monthly_data[month]["expense"]
        )
        for month in months
    ]

    # --------------------------------------------------------
    # FORECAST
    # --------------------------------------------------------

    income_forecast = forecast_series(
        income_values,
        periods,
    )

    expense_forecast = forecast_series(
        expense_values,
        periods,
    )

    # --------------------------------------------------------
    # LAST HISTORICAL MONTH
    # --------------------------------------------------------

    last_month = pd.Timestamp(
        months[-1]
    )

    # --------------------------------------------------------
    # DELETE OLD FORECASTS
    # --------------------------------------------------------

    FinancialForecast.objects.all().delete()

    # --------------------------------------------------------
    # SAVE NEW FORECASTS
    # --------------------------------------------------------

    forecasts = []

    for i in range(periods):

        forecast_month = (
            last_month
            + pd.DateOffset(
                months=i + 1
            )
        ).date()

        predicted_income = Decimal(
            str(
                round(
                    income_forecast[i],
                    2,
                )
            )
        )

        predicted_expense = Decimal(
            str(
                round(
                    expense_forecast[i],
                    2,
                )
            )
        )

        # ----------------------------------------------------
        # CREATE FORECAST RECORD
        # ----------------------------------------------------

        forecast = FinancialForecast.objects.create(
            forecast_month=forecast_month,
            predicted_income=predicted_income,
            predicted_expense=predicted_expense,
            generated_at=timezone.now(),
        )

        forecasts.append(
            forecast
        )

    # --------------------------------------------------------
    # SAFETY CHECK
    # --------------------------------------------------------

    if len(forecasts) != periods:
        raise RuntimeError(
            "Forecast generation did not create "
            f"exactly {periods} rows."
        )

    return forecasts
