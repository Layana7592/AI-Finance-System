"""Export separate, time-validated research evidence WITHOUT overwriting benchmarks.

    python manage.py export_research_evidence --output evidence/controlled_studies.json

The original 50k in-sample experiment is unchanged; this additional command
performs a chronological holdout on those rows AND on an independently
generated behaviour-only synthetic sample. Forecasts include strictly paired
SARIMA/Seasonal-Naive metrics, residuals and failed validation months.
"""
import json
import os
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from finance.models import Transaction
from finance.services.forecast_service import evaluate_forecast_models
from finance.services.research_experiments import (
    evaluate_behavioural_study,
    evaluate_chronological_holdout,
)


class Command(BaseCommand):
    help = "Generate original-data holdout, behavioural-anomaly and paired forecast evidence"

    def add_arguments(self, parser):
        parser.add_argument("--output", required=True)
        parser.add_argument("--seed", type=int, default=42)
        parser.add_argument("--behavioural-transactions", type=int, default=6000)
        parser.add_argument("--behavioural-anomalies", type=int, default=90)
        parser.add_argument("--estimators", type=int, default=160)

    def handle(self, *args, **options):
        rows = list(Transaction.objects.order_by("transaction_time", "transaction_id"))
        if len(rows) < 100:
            raise CommandError("Bootstrap 100 or more synthetic transactions first.")
        self.stdout.write(f"Time-validating {len(rows):,} existing synthetic transactions...")
        previous = evaluate_chronological_holdout(
            rows, seed=options["seed"], estimators=options["estimators"],
        )
        self.stdout.write("Generating independent behavioural-only study...")
        behavioural = evaluate_behavioural_study(
            seed=options["seed"], accounts=60,
            transactions=options["behavioural_transactions"],
            anomalies=options["behavioural_anomalies"],
            estimators=options["estimators"],
        )
        self.stdout.write("Evaluating paired seasonal forecasting windows...")
        forecasts = evaluate_forecast_models()
        if forecasts.get("status") != "success":
            raise CommandError("Forecast series unavailable for comparison.")
        for series in ("income", "expense"):
            validation = forecasts[series]["validation"]
            if validation["paired_comparison"]["observations"] != validation["sarima_observations"]:
                raise CommandError("Paired and SARIMA observation counts disagree.")
            if len(validation["windows"]) != validation["observations"]:
                raise CommandError("Forecast window counts disagree.")

        report = {
            "study_version": "ControlledStudies-v1",
            "source": "Synthetic banking data; no real-world fraud labels",
            "original_experiment_preserved": True,
            "captured_at_utc": timezone.now().isoformat(),
            "commit_sha": os.getenv("GITHUB_SHA", "local-unpinned"),
            "original_data_chronological_holdout": previous,
            "separate_behavioural_holdout": behavioural,
            "forecast_matched_window_comparison": forecasts,
            "interpretation_rules": [
                "Do not compare this held-out evaluation directly to the previous in-sample F1 as identical experiments.",
                "The deliberately synthetic behavioural-only cases are hypotheses, not verified banking fraud.",
                "The normal and anomalous amounts share the same generating distribution, but random samples differ.",
                "Compare Seasonal-Naive and SARIMA errors ONLY on the same successful timestamps; show SARIMA failures separately.",
                "All classification metrics must be accompanied by confusion counts and event prevalence.",
                "Anomaly feature median differences are descriptive; no causal feature-importance claim is made.",
                "No data were written, reclassified or replaced by this evidence exporter.",
            ],
        }
        target = Path(options["output"])
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(report, sort_keys=True, indent=2, allow_nan=False, default=str),
            encoding="utf-8",
        )
        self.stdout.write(self.style.SUCCESS(f"Controlled research evidence saved: {target}"))
