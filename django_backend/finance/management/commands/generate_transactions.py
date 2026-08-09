
from django.core.management.base import BaseCommand
from django.db import transaction as db_transaction
from django.utils import timezone

from faker import Faker
from decimal import Decimal
from datetime import datetime
import random
import math

from finance.models import Transaction, Account


class Command(BaseCommand):
    help = "Generate realistic synthetic financial transactions"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=50000,
            help="Number of transactions to generate",
        )

    def handle(self, *args, **options):
        fake = Faker()
        count = options["count"]

        # --------------------------------------------------
        # GET EXISTING ACCOUNTS
        # --------------------------------------------------

        accounts = list(Account.objects.all())

        if not accounts:
            self.stdout.write(
                self.style.ERROR(
                    "No accounts found. Generate accounts first."
                )
            )
            return

        self.stdout.write(
            f"Generating {count:,} transactions..."
        )

        # --------------------------------------------------
        # TRANSACTION TYPES
        # --------------------------------------------------

        transaction_types = [
            "Deposit",
            "Withdrawal",
            "Transfer",
            "Payment",
            "Purchase",
        ]

        statuses = [
            "Completed",
            "Completed",
            "Completed",
            "Completed",
            "Pending",
            "Failed",
        ]

        # --------------------------------------------------
        # 24-MONTH PERIOD
        # --------------------------------------------------

        start_date = datetime(2024, 1, 1)
        end_date = datetime(2025, 12, 31, 23, 59, 59)

        transactions = []

        anomaly_count = 0

        # --------------------------------------------------
        # GENERATE TRANSACTIONS
        # --------------------------------------------------

        for i in range(count):

            account = random.choice(accounts)

            # ----------------------------------------------
            # GENERATE DATE
            # ----------------------------------------------

            transaction_time = timezone.make_aware(
                fake.date_time_between(
                    start_date=start_date,
                    end_date=end_date
                )
            )

            month = transaction_time.month

            # ----------------------------------------------
            # REALISTIC SEASONALITY
            # ----------------------------------------------
            #
            # Higher transaction activity during:
            # - March/April
            # - October/November/December
            #
            # Lower activity during:
            # - June/July/August
            #
            # This creates a meaningful forecasting signal.
            # ----------------------------------------------

            seasonal_factor = {
                1: 1.00,
                2: 0.95,
                3: 1.15,
                4: 1.20,
                5: 1.05,
                6: 0.90,
                7: 0.85,
                8: 0.88,
                9: 1.00,
                10: 1.15,
                11: 1.25,
                12: 1.35,
            }.get(month, 1.0)

            # ----------------------------------------------
            # BASE AMOUNT
            # ----------------------------------------------

            base_amount = random.uniform(
                500,
                75000
            )

            # Apply seasonal effect
            amount = base_amount * seasonal_factor

            # Add small random variation
            noise = random.uniform(
                0.85,
                1.15
            )

            amount *= noise

            # ----------------------------------------------
            # TRANSACTION TYPE
            # ----------------------------------------------

            transaction_type = random.choice(
                transaction_types
            )

            # ----------------------------------------------
            # ANOMALY GENERATION
            # ----------------------------------------------
            #
            # Approximately 1% anomalies.
            #
            # Ground truth:
            # 0 = normal
            # 1 = anomaly
            # ----------------------------------------------

            is_anomaly = 0

            if random.random() < 0.01:

                is_anomaly = 1
                anomaly_count += 1

                # Make anomalous transaction unusual
                anomaly_type = random.choice(
                    [
                        "large_amount",
                        "unusual_amount",
                        "unusual_transaction",
                    ]
                )

                if anomaly_type == "large_amount":
                    amount *= random.uniform(
                        5,
                        15
                    )

                elif anomaly_type == "unusual_amount":
                    amount = random.uniform(
                        150000,
                        500000
                    )

                elif anomaly_type == "unusual_transaction":
                    transaction_type = random.choice(
                        [
                            "Transfer",
                            "Withdrawal",
                        ]
                    )

                    amount *= random.uniform(
                        3,
                        10
                    )

            # ----------------------------------------------
            # LIMIT AMOUNT
            # ----------------------------------------------

            amount = Decimal(
                str(round(amount, 2))
            )

            # ----------------------------------------------
            # CREATE TRANSACTION OBJECT
            # ----------------------------------------------

            transactions.append(
                Transaction(
                    account=account,
                    amount=amount,
                    transaction_type=transaction_type,
                    merchant=fake.company(),
                    location=fake.city(),
                    transaction_time=transaction_time,
                    status=random.choice(statuses),
                    is_anomaly=is_anomaly,
                )
            )

            # ----------------------------------------------
            # BULK INSERT IN BATCHES
            # ----------------------------------------------

            if len(transactions) >= 1000:

                with db_transaction.atomic():
                    Transaction.objects.bulk_create(
                        transactions,
                        batch_size=1000
                    )

                transactions.clear()

                self.stdout.write(
                    f"Generated {i + 1:,}/{count:,}"
                )

        # --------------------------------------------------
        # INSERT REMAINING TRANSACTIONS
        # --------------------------------------------------

        if transactions:

            with db_transaction.atomic():
                Transaction.objects.bulk_create(
                    transactions,
                    batch_size=1000
                )

        # --------------------------------------------------
        # FINAL RESULT
        # --------------------------------------------------

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully generated {count:,} transactions!"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Hidden anomalies: {anomaly_count}"
            )
        )
