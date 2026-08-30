from django.db.models import Sum
from django.db.models.functions import TruncMonth

from finance.models import Transaction, FinancialForecast
from finance.services.fraud_service import evaluate_fraud_models
from finance.services.forecast_service import evaluate_forecast_models


def get_dashboard_data():
    """
    Return verified analytics for the AI Finance System dashboard.

    The dashboard contains:

    1. Transaction summary
    2. Historical monthly income/expense
    3. Fraud/anomaly model evaluation
    4. Forecast model evaluation
    5. Saved 2026 forecasts
    6. Forecasting system information

    Important:
    All analytical metrics are calculated by Python services.
    Gemini is not used to calculate numerical metrics.
    """

    # ============================================================
    # 1. TRANSACTION SUMMARY
    # ============================================================

    total_transactions = Transaction.objects.count()

    actual_anomalies = Transaction.objects.filter(
        is_anomaly=1
    ).count()

    anomaly_percentage = (
        (actual_anomalies / total_transactions) * 100
        if total_transactions > 0
        else 0
    )

    # ============================================================
    # 2. TOTAL INCOME
    # ============================================================

    income_total = (
        Transaction.objects
        .filter(
            transaction_type__iexact="Deposit"
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )

    # ============================================================
    # 3. TOTAL EXPENSE
    # ============================================================

    expense_total = (
        Transaction.objects
        .filter(
            transaction_type__in=[
                "Withdrawal",
                "Payment",
                "Purchase",
            ]
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )

    # ============================================================
    # 4. MONTHLY INCOME / EXPENSE
    # ============================================================

    monthly_rows = (
        Transaction.objects
        .annotate(
            month=TruncMonth("transaction_time")
        )
        .values(
            "month",
            "transaction_type",
        )
        .annotate(
            total=Sum("amount")
        )
        .order_by(
            "month"
        )
    )

    monthly_data = {}

    for row in monthly_rows:

        month = row["month"]

        if month is None:
            continue

        if month not in monthly_data:
            monthly_data[month] = {
                "income": 0.0,
                "expense": 0.0,
            }

        transaction_type = str(
            row["transaction_type"]
        ).strip().lower()

        total = float(
            row["total"] or 0
        )

        # -------------------------
        # Income
        # -------------------------

        if transaction_type == "deposit":

            monthly_data[month]["income"] += total

        # -------------------------
        # Expense
        # -------------------------

        elif transaction_type in {
            "withdrawal",
            "payment",
            "purchase",
        }:

            monthly_data[month]["expense"] += total

    monthly_trends = []

    for month in sorted(
        monthly_data.keys()
    ):

        monthly_trends.append(
            {
                "month": month.strftime(
                    "%Y-%m"
                ),
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

    # ============================================================
    # 5. VERIFIED FRAUD MODEL EVALUATION
    # ============================================================

    fraud_evaluation = evaluate_fraud_models()

    # ============================================================
    # 6. VERIFIED FORECAST MODEL EVALUATION
    # ============================================================

    forecast_evaluation = evaluate_forecast_models()

    # ============================================================
    # 7. SAVED 2026 FORECASTS
    # ============================================================

    forecasts = (
        FinancialForecast.objects
        .all()
        .order_by("forecast_month")
    )

    forecast_data = []

    for forecast in forecasts:

        if forecast.forecast_month.year != 2026:
            continue

        forecast_data.append(
            {
                "month": forecast.forecast_month.strftime(
                    "%Y-%m"
                ),
                "predicted_income": round(
                    float(
                        forecast.predicted_income
                    ),
                    2,
                ),
                "predicted_expense": round(
                    float(
                        forecast.predicted_expense
                    ),
                    2,
                ),
            }
        )

    # ============================================================
    # 8. FORECAST SYSTEM INFORMATION
    # ============================================================

    forecast_dataset = (
        forecast_evaluation.get(
            "dataset",
            {}
        )
    )

    historical_months = int(
        forecast_dataset.get(
            "months",
            24
        )
    )

    training_months = int(
        forecast_dataset.get(
            "training_months",
            12
        )
    )

    validation_months = int(
        forecast_dataset.get(
            "validation_months",
            12
        )
    )

    forecast_horizon = 12

    # ============================================================
    # 9. FINAL RESPONSE
    # ============================================================

    return {
        "summary": {
            "total_transactions": (
                total_transactions
            ),
            "actual_anomalies": (
                actual_anomalies
            ),
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

        "monthly_trends": monthly_trends,

        "forecasts": forecast_data,

        "fraud_evaluation": fraud_evaluation,

        "forecast_evaluation": forecast_evaluation,

        "system_info": {
            "historical_months": historical_months,
            "training_months": training_months,
            "validation_months": validation_months,
            "forecast_horizon": forecast_horizon,
        },
    }