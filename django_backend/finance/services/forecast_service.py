from decimal import Decimal
from django.utils import timezone

import numpy as np
import pandas as pd
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from statsmodels.tsa.statespace.sarimax import SARIMAX

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
        dtype="float64"
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
                len(series) - seasonal_period
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
    Forecast using one SARIMA model.

    Model:

        SARIMA(1,0,0)(1,0,0,12)

    The same model is used for both validation
    and final forecasting.
    """

    series = pd.Series(
        train_series,
        dtype="float64"
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

    try:

        model = SARIMAX(
            series,
            order=(1, 0, 0),
            seasonal_order=(1, 0, 0, 12),
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

        # Safe fallback if SARIMA fails.

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
        dtype=float
    )

    predicted = np.asarray(
        predicted,
        dtype=float
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
# CHRONOLOGICAL MODEL VALIDATION
# ============================================================

def evaluate_series_models(
    series,
    train_periods=12,
    validation_periods=12,
):
    """
    Compare Seasonal-Naive and SARIMA using
    chronological validation.

    With 24 months:

        Training:
            First 12 months

        Validation:
            Last 12 months

    No random train/test splitting is used.
    """

    series = pd.Series(
        series,
        dtype="float64"
    ).reset_index(drop=True)

    required_length = (
        train_periods
        + validation_periods
    )

    if len(series) < required_length:

        raise ValueError(
            f"At least {required_length} months "
            "are required for chronological validation."
        )

    # --------------------------------------------------------
    # CHRONOLOGICAL SPLIT
    # --------------------------------------------------------

    train = series.iloc[
        :train_periods
    ]

    validation = series.iloc[
        train_periods:
        train_periods + validation_periods
    ]

    actual = validation.tolist()

    # --------------------------------------------------------
    # SEASONAL-NAIVE
    # --------------------------------------------------------

    seasonal_naive_predictions = (
        seasonal_naive_forecast(
            train,
            periods=validation_periods,
            seasonal_period=12,
        )
    )

    seasonal_naive_metrics = (
        calculate_forecast_metrics(
            actual,
            seasonal_naive_predictions,
        )
    )

    # --------------------------------------------------------
    # SARIMA
    # --------------------------------------------------------

    sarima_predictions = (
        sarima_forecast(
            train,
            periods=validation_periods,
        )
    )

    sarima_metrics = (
        calculate_forecast_metrics(
            actual,
            sarima_predictions,
        )
    )

    # --------------------------------------------------------
    # DETERMINE BETTER MODEL
    # --------------------------------------------------------

    # MAE is used as the primary selection metric.

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

    return {
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
            for value in actual
        ],

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

    using chronological validation.

    The first 12 months are training data and
    the final 12 months are validation data.
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
        dtype="float64"
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
            seasonal_order=(1, 0, 0, 12),
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
                    upper_limit
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
    periods=12
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
        periods
    )

    expense_forecast = forecast_series(
        expense_values,
        periods
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
                    2
                )
            )
        )

        predicted_expense = Decimal(
            str(
                round(
                    expense_forecast[i],
                    2
                )
            )
        )

<<<<<<< ours
        forecast = (
            FinancialForecast.objects.create(
                forecast_month=forecast_month,
                predicted_income=predicted_income,
                predicted_expense=predicted_expense,
                generated_at=timezone.now(),
            )
=======
        forecast = FinancialForecast.objects.create(
            forecast_month=forecast_month,
            predicted_income=predicted_income,
            predicted_expense=predicted_expense,
            generated_at=timezone.now()
>>>>>>> theirs
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