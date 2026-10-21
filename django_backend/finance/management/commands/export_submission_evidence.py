"""Export reproducible, synthetic-data evidence for the academic report.

Usage (after PostgreSQL migrations and bootstrap_demo_data):
    python manage.py export_submission_evidence --output evidence/results.json

This never calls Gemini and never alters transaction or prediction records.
"""
import json
import os
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from finance.models import (
    Account, Alert, AuditLog, Branch, FinancialForecast, FraudPrediction,
    Transaction, User,
)
from finance.services.forecast_service import evaluate_forecast_models
from finance.services.fraud_service import evaluate_fraud_models


class Command(BaseCommand):
    help = "Export verifiable synthetic academic demonstration results to JSON"

    def add_arguments(self, parser):
        parser.add_argument("--output", type=str, required=True)

    def handle(self, *args, **options):
        transaction_count = Transaction.objects.count()
        if transaction_count == 0:
            raise CommandError("No transactions found. Bootstrap demo data first.")

        counts = {
            "users": User.objects.count(),
            "branches": Branch.objects.count(),
            "accounts": Account.objects.count(),
            "transactions": transaction_count,
            "ground_truth_anomalies": Transaction.objects.filter(is_anomaly=1).count(),
            "persisted_predictions": FraudPrediction.objects.count(),
            "open_alerts": Alert.objects.filter(is_resolved=False).count(),
            "audit_logs": AuditLog.objects.count(),
            "saved_forecasts": FinancialForecast.objects.count(),
        }
        forecast_months = list(
            FinancialForecast.objects.order_by("forecast_month").values_list(
                "forecast_month", flat=True
            )
        )
        self.stdout.write("Evaluating Isolation Forest and statistical baseline...")
        fraud_results = evaluate_fraud_models()
        self.stdout.write("Evaluating Seasonal-Naive and SARIMA...")
        forecast_results = evaluate_forecast_models()

        if fraud_results.get("dataset") != transaction_count:
            raise CommandError("Fraud evaluation transaction count mismatch.")
        if fraud_results.get("actual_anomalies") != counts["ground_truth_anomalies"]:
            raise CommandError("Ground-truth anomaly counts disagree.")

        evidence = {
            "source": "Academic synthetic banking demonstration; NOT real bank data",
            "captured_at_utc": timezone.now().isoformat(),
            "commit_sha": os.getenv("GITHUB_SHA", "local-unpinned"),
            "counts": counts,
            "forecast_months": [value.isoformat() for value in forecast_months],
            "fraud_evaluation": fraud_results,
            "forecast_evaluation": forecast_results,
            "limitations": [
                "Synthetic anomaly labels are dominated by exaggerated amounts.",
                "Isolation Forest benchmark is evaluated on the data used to fit it.",
                "Live behavioural risk scores are not calibrated fraud probabilities.",
                "SARIMA can be unstable with short monthly histories.",
                "Historical README numbers must not be substituted for this run's results.",
            ],
        }
        path = Path(options["output"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(evidence, indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )
        self.stdout.write(self.style.SUCCESS(
            f"Evidence saved: {path}; {transaction_count} synthetic transactions"
        ))
