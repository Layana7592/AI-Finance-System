from django.db.models import Sum
from django.db.models.functions import TruncMonth

from finance.models import Transaction, FinancialForecast
from finance.services.fraud_service import evaluate_fraud_models
from finance.services.forecast_service import evaluate_forecast_models


def get_dashboard_data():
    """
    Return verified data for the small finance dashboard.

    The dashboard uses:
    - Database transaction totals
    - Verified fraud-model evaluation
    - Verified forecast-model evaluation
    - Saved 2026 forecasts
    """

    # ========================================================
    # TRANSACTION SUMMARY
    # ========================================================

    total_transactions = Transaction.objects.count()

    actual_anomalies = Transaction.objects.filter(
        is_anomaly=1
    ).count()

    anomaly_percentage = (
        (actual_anomalies / total_transactions) * 100
        if total_transactions
        else 0
    )

    # ========================================================
    # TOTAL INCOME / EXPENSE
    # ========================================================

    income_total = (
        Transaction.objects
        .filter(transaction_type__iexact="Deposit")
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )

    expense_total = (
        Transaction.objects
        .filter(
            transaction_type__in=[
                "Withdrawal",
                "Payment",
                "Purchase",
            ]
        )
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )

    # ========================================================
    # MONTHLY TRENDS
    # ========================================================

    monthly_rows = (
        Transaction.objects
        .annotate(month=TruncMonth("transaction_time"))
        .values("month", "transaction_type")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )

    monthly_data = {}

    for row in monthly_rows:
        month = row["month"]

        if month not in monthly_data:
            monthly_data[month] = {
                "income": 0,
                "expense": 0,
            }

        transaction_type = str(
            row["transaction_type"]
        ).lower()

        total = float(row["total"] or 0)

        if transaction_type == "deposit":
            monthly_data[month]["income"] += total

        elif transaction_type in [
            "withdrawal",
            "payment",
            "purchase",
        ]:
            monthly_data[month]["expense"] += total

    monthly_trends = []

    for month in sorted(monthly_data.keys()):
        monthly_trends.append(
            {
                "month": month.strftime("%Y-%m"),
                "income": round(
                    monthly_data[month]["income"],
                    2,
                ),
                "expense": round(
                    monthly_data[month]["expense"],
                    2,
                ),
            }
        )

    # ========================================================
    # VERIFIED FRAUD EVALUATION
    # ========================================================

    fraud_evaluation = evaluate_fraud_models()

    # ========================================================
    # VERIFIED FORECAST EVALUATION
    # ========================================================

    forecast_evaluation = evaluate_forecast_models()

    # ========================================================
    # SAVED 2026 FORECASTS
    # ========================================================

    forecasts = (
        FinancialForecast.objects
        .all()
        .order_by("forecast_month")
    )

    forecast_data = [
        {
            "month": forecast.forecast_month.strftime(
                "%Y-%m"
            ),
            "predicted_income": float(
                forecast.predicted_income
            ),
            "predicted_expense": float(
                forecast.predicted_expense
            ),
        }
        for forecast in forecasts
    ]

    # ========================================================
    # FINAL DASHBOARD DATA
    # ========================================================

    return {
        "summary": {
            "total_transactions": total_transactions,
            "actual_anomalies": actual_anomalies,
            "anomaly_percentage": round(
                anomaly_percentage,
                2,
            ),
            "total_income": round(
                float(income_total),
                2,
            ),
            "total_expense": round(
                float(expense_total),
                2,
            ),
        },

        "fraud_evaluation": fraud_evaluation,

        "forecast_evaluation": forecast_evaluation,

        "monthly_trends": monthly_trends,

        "forecasts": forecast_data,
    }