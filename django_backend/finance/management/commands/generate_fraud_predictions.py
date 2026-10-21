"""Run the expensive Isolation Forest fit as a deliberate offline batch job.

Use this after bootstrapping demo data, never inside a transaction POST:
    python manage.py generate_fraud_predictions
"""
from django.core.management.base import BaseCommand

from finance.services.fraud_service import generate_fraud_predictions


class Command(BaseCommand):
    help = "Generate or refresh batch Isolation Forest predictions for demo data"

    def handle(self, *args, **options):
        count = generate_fraud_predictions()
        self.stdout.write(self.style.SUCCESS(
            f"Batch Isolation Forest predictions refreshed: {count}"
        ))
