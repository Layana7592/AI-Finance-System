import pandas as pd
from django.utils import timezone
from statsmodels.tsa.arima.model import ARIMA

from finance.models import Transaction, FinancialForecast


def generate_forecast():

    # -----------------------------------------
    # 1. Get transactions from PostgreSQL
    # -----------------------------------------

    transactions = Transaction.objects.values(
        "transaction_time",
        "amount"
    )

    if not transactions:
        raise ValueError("No transaction data found.")

    df = pd.DataFrame(list(transactions))

    # -----------------------------------------
    # 2. Clean the data
    # -----------------------------------------

    df["transaction_time"] = pd.to_datetime(
        df["transaction_time"]
    )

    df["amount"] = pd.to_numeric(
        df["amount"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["transaction_time", "amount"]
    )

    # -----------------------------------------
    # 3. Convert transactions to monthly totals
    # -----------------------------------------

    df["month"] = (
        df["transaction_time"]
        .dt.to_period("M")
        .dt.to_timestamp()
    )

    monthly_data = (
        df.groupby("month")["amount"]
        .sum()
        .sort_index()
    )

    if len(monthly_data) < 3:
        raise ValueError(
            "Not enough monthly data for ARIMA forecasting."
        )

    print("Monthly transaction data:")
    print(monthly_data)

    # -----------------------------------------
    # 4. Train ARIMA
    # -----------------------------------------

    print("\nTraining ARIMA model...")

    model = ARIMA(
        monthly_data,
        order=(1, 1, 1)
    )

    model_fit = model.fit()

    print("ARIMA model trained successfully!")

    # -----------------------------------------
    # 5. Forecast next 12 months
    # -----------------------------------------

    forecast_values = model_fit.forecast(
        steps=12
    )

    last_month = monthly_data.index.max()

    forecast_dates = pd.date_range(
        start=last_month + pd.offsets.MonthBegin(1),
        periods=12,
        freq="MS"
    )

    # -----------------------------------------
    # 6. Remove previous forecasts
    # -----------------------------------------

    FinancialForecast.objects.all().delete()

    # -----------------------------------------
    # 7. Save new forecasts
    # -----------------------------------------

    forecast_objects = []

    for forecast_date, value in zip(
        forecast_dates,
        forecast_values
    ):

        predicted_income = float(value)

        predicted_expense = (
            predicted_income * 0.70
        )

        forecast_objects.append(
            FinancialForecast(
                forecast_month=forecast_date.date(),
                predicted_income=predicted_income,
                predicted_expense=predicted_expense,
                generated_at=timezone.now()
            )
        )

    FinancialForecast.objects.bulk_create(
        forecast_objects
    )

    print(
        "\n12-month forecast saved successfully!"
    )

    # -----------------------------------------
    # 8. Return JSON-friendly results
    # -----------------------------------------

    results = []

    for forecast_date, value in zip(
        forecast_dates,
        forecast_values
    ):

        predicted_income = float(value)

        results.append({
            "forecast_month": forecast_date.strftime(
                "%Y-%m-%d"
            ),
            "predicted_income": round(
                predicted_income,
                2
            ),
            "predicted_expense": round(
                predicted_income * 0.70,
                2
            )
        })

    return results