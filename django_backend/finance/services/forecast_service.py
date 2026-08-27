from decimal import Decimal
from django.utils import timezone

import pandas as pd
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from statsmodels.tsa.statespace.sarimax import SARIMAX

from finance.models import Transaction, FinancialForecast


def get_monthly_data():
    """
    Retrieve monthly income and expense totals
    from transaction data.
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

        # Income
        if transaction_type == "deposit":
            data[month]["income"] += total

        # Expenses
        elif transaction_type in [
            "withdrawal",
            "payment",
            "purchase",
        ]:
            data[month]["expense"] += total

        # Transfers are ignored
        # because they are not actual income or expense.

    return data


def forecast_series(series, periods=12):
    """
    Forecast a monthly time series using SARIMA.

    Uses the last 12 months as a fallback if
    the SARIMA model cannot be fitted.
    """

    series = pd.Series(
        series,
        dtype="float64"
    )

    if len(series) < 12:
        return [float(series.mean())] * periods

    try:
        model = SARIMAX(
            series,
            order=(1, 1, 1),
            seasonal_order=(1, 1, 1, 12),
            enforce_stationarity=False,
            enforce_invertibility=False,
        )

        fitted_model = model.fit(
            disp=False
        )

        forecast = fitted_model.forecast(
            steps=periods
        )

        return [
            max(0.0, float(value))
            for value in forecast
        ]

    except Exception:
        # Seasonal-naive fallback
        last_12 = series.iloc[-12:].tolist()

        result = []

        for i in range(periods):
            result.append(
                max(
                    0.0,
                    float(last_12[i % 12])
                )
            )

        return result


def generate_forecast(periods=12):
    """
    Generate future monthly income and expense
    forecasts and store them in FinancialForecast.
    """

    monthly_data = get_monthly_data()

    if len(monthly_data) < 12:
        raise ValueError(
            "At least 12 months of historical "
            "transaction data is required."
        )

    # Sort historical months
    months = sorted(
        monthly_data.keys()
    )

    # Historical income
    income_values = [
        float(
            monthly_data[month]["income"]
        )
        for month in months
    ]

    # Historical expense
    expense_values = [
        float(
            monthly_data[month]["expense"]
        )
        for month in months
    ]

    # Generate forecasts
    income_forecast = forecast_series(
        income_values,
        periods
    )

    expense_forecast = forecast_series(
        expense_values,
        periods
    )

    # Last available historical month
    last_month = pd.Timestamp(
        months[-1]
    )

    # Remove previous forecasts
    FinancialForecast.objects.all().delete()

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

        forecast = FinancialForecast.objects.create(
            forecast_month=forecast_month,
            predicted_income=predicted_income,
            predicted_expense=predicted_expense,
            generated_at=timezone.now()
        )

        forecasts.append(
            forecast
        )

    return forecasts