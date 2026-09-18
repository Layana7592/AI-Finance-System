from datetime import datetime, timedelta
from decimal import Decimal

import random

from django.core.management.base import BaseCommand
from django.db import transaction as db_transaction
from django.utils import timezone

from faker import Faker

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

        parser.add_argument(
            "--anomalies",
            type=int,
            default=500,
            help="Exact number of anomalous transactions",
        )

        parser.add_argument(
            "--seed",
            type=int,
            default=42,
            help="Random seed for reproducible data",
        )

    def handle(self, *args, **options):

        count = options["count"]
        anomaly_target = options["anomalies"]
        seed = options["seed"]

        # --------------------------------------------------
        # VALIDATION
        # --------------------------------------------------

        if count <= 0:
            self.stdout.write(
                self.style.ERROR(
                    "--count must be greater than 0."
                )
            )
            return

        if anomaly_target < 0:
            self.stdout.write(
                self.style.ERROR(
                    "--anomalies cannot be negative."
                )
            )
            return

        if anomaly_target > count:
            self.stdout.write(
                self.style.ERROR(
                    "--anomalies cannot be greater than --count."
                )
            )
            return

        # --------------------------------------------------
        # REPRODUCIBLE RANDOMNESS
        # --------------------------------------------------

        random.seed(seed)
        Faker.seed(seed)

        fake = Faker()

        # --------------------------------------------------
        # GET EXISTING ACCOUNTS
        # --------------------------------------------------

        accounts = list(
            Account.objects.all()
        )

        if not accounts:

            self.stdout.write(
                self.style.ERROR(
                    "No accounts found. Generate accounts first."
                )
            )

            return

        # --------------------------------------------------
        # ACCOUNT BEHAVIOUR PROFILES
        # --------------------------------------------------
        #
        # Every account receives:
        #
        # - normal merchants
        # - normal locations
        #
        # This allows fraud detection models to learn
        # account-level behaviour.
        # --------------------------------------------------

        account_merchants = {}
        account_locations = {}

        used_merchants = set()
        used_locations = set()

        for account in accounts:

            merchants = []

            while len(merchants) < 3:

                merchant = fake.company()

                if merchant not in used_merchants:

                    merchants.append(merchant)
                    used_merchants.add(merchant)

            locations = []

            while len(locations) < 3:

                location = fake.city()

                if location not in used_locations:

                    locations.append(location)
                    used_locations.add(location)

            account_merchants[
                account.account_id
            ] = merchants

            account_locations[
                account.account_id
            ] = locations

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

        # --------------------------------------------------
        # TRANSACTION STATUSES
        # --------------------------------------------------

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

        start_date = datetime(
            2024,
            1,
            1
        )

        end_date = datetime(
            2025,
            12,
            31,
            23,
            59,
            59
        )

        # --------------------------------------------------
        # EXACT ANOMALY POSITIONS
        # --------------------------------------------------
        #
        # Instead of random 1% probability, choose exactly
        # the requested number of anomaly rows.
        #
        # Example:
        #
        # 50,000 transactions
        # 500 anomalies
        #
        # = exactly 1%
        # --------------------------------------------------

        anomaly_indices = set(
            random.sample(
                range(count),
                anomaly_target
            )
        )

        # --------------------------------------------------
        # STORAGE
        # --------------------------------------------------

        transactions = []

        generated_anomalies = 0

        # --------------------------------------------------
        # GENERATE TRANSACTIONS
        # --------------------------------------------------

        for i in range(count):

            # --------------------------------------------------
            # SELECT ACCOUNT
            # --------------------------------------------------

            account = random.choice(
                accounts
            )

            account_id = account.account_id

            # --------------------------------------------------
            # GENERATE DATE
            # --------------------------------------------------

            transaction_time = timezone.make_aware(
                fake.date_time_between(
                    start_date=start_date,
                    end_date=end_date
                )
            )

            month = transaction_time.month

            # --------------------------------------------------
            # REALISTIC SEASONALITY
            # --------------------------------------------------

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
            }.get(
                month,
                1.0
            )

            # --------------------------------------------------
            # BASE AMOUNT
            # --------------------------------------------------

            base_amount = random.uniform(
                500,
                75000
            )

            amount = (
                base_amount
                * seasonal_factor
            )

            # --------------------------------------------------
            # SMALL NORMAL VARIATION
            # --------------------------------------------------

            noise = random.uniform(
                0.85,
                1.15
            )

            amount *= noise

            # --------------------------------------------------
            # TRANSACTION TYPE
            # --------------------------------------------------

            transaction_type = random.choice(
                transaction_types
            )

            # --------------------------------------------------
            # NORMAL MERCHANT
            # --------------------------------------------------

            merchant = random.choice(
                account_merchants[
                    account_id
                ]
            )

            # --------------------------------------------------
            # NORMAL LOCATION
            # --------------------------------------------------

            location = random.choice(
                account_locations[
                    account_id
                ]
            )

            # --------------------------------------------------
            # GROUND TRUTH
            # --------------------------------------------------

            is_anomaly = 0

            # --------------------------------------------------
            # ANOMALY GENERATION
            # --------------------------------------------------

            if i in anomaly_indices:

                is_anomaly = 1
                generated_anomalies += 1

                # --------------------------------------------------
                # SELECT ANOMALY TYPE
                # --------------------------------------------------

                anomaly_type = random.choice(
                    [
                        "large_amount",
                        "unusual_amount",
                        "unusual_transaction",
                        "unusual_merchant",
                        "unusual_location",
                        "unusual_time",
                        "high_frequency",
                    ]
                )

                # --------------------------------------------------
                # LARGE AMOUNT
                # --------------------------------------------------

                if anomaly_type == "large_amount":

                    amount *= random.uniform(
                        5,
                        15
                    )

                # --------------------------------------------------
                # UNUSUAL AMOUNT
                # --------------------------------------------------

                elif anomaly_type == "unusual_amount":

                    amount = random.uniform(
                        150000,
                        500000
                    )

                # --------------------------------------------------
                # UNUSUAL TRANSACTION TYPE
                # --------------------------------------------------

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

                # --------------------------------------------------
                # UNUSUAL MERCHANT
                # --------------------------------------------------
                #
                # Merchant is intentionally outside the account's
                # normal merchant profile.
                # --------------------------------------------------

                elif anomaly_type == "unusual_merchant":

                    merchant = fake.company()

                    while (
                        merchant in
                        account_merchants[
                            account_id
                        ]
                    ):

                        merchant = fake.company()

                # --------------------------------------------------
                # UNUSUAL LOCATION
                # --------------------------------------------------
                #
                # Location is intentionally outside the account's
                # normal location profile.
                # --------------------------------------------------

                elif anomaly_type == "unusual_location":

                    location = fake.city()

                    while (
                        location in
                        account_locations[
                            account_id
                        ]
                    ):

                        location = fake.city()

                # --------------------------------------------------
                # UNUSUAL TIME
                # --------------------------------------------------
                #
                # Transactions between midnight and 5 AM are
                # unusual for this synthetic banking dataset.
                # --------------------------------------------------

                elif anomaly_type == "unusual_time":

                    unusual_hour = random.randint(
                        0,
                        5
                    )

                    transaction_time = (
                        transaction_time.replace(
                            hour=unusual_hour,
                            minute=random.randint(
                                0,
                                59
                            ),
                            second=random.randint(
                                0,
                                59
                            )
                        )
                    )

                # --------------------------------------------------
                # HIGH FREQUENCY / BURST
                # --------------------------------------------------
                #
                # Create a transaction very close to the previous
                # time point. This gives the later fraud service
                # a useful signal for transaction frequency.
                # --------------------------------------------------

                elif anomaly_type == "high_frequency":

                    transaction_time = (
                        transaction_time
                        + timedelta(
                            seconds=random.randint(
                                1,
                                20
                            )
                        )
                    )

                    amount *= random.uniform(
                        1.5,
                        4
                    )

            # --------------------------------------------------
            # ROUND AMOUNT
            # --------------------------------------------------

            amount = Decimal(
                str(
                    round(
                        amount,
                        2
                    )
                )
            )

            # --------------------------------------------------
            # CREATE TRANSACTION OBJECT
            # --------------------------------------------------

            transactions.append(
                Transaction(
                    account=account,
                    amount=amount,
                    transaction_type=transaction_type,
                    merchant=merchant,
                    location=location,
                    transaction_time=transaction_time,
                    status=random.choice(statuses),
                    is_anomaly=is_anomaly,
                )
            )

            # --------------------------------------------------
            # BULK INSERT
            # --------------------------------------------------

            if len(transactions) >= 1000:

                with db_transaction.atomic():

                    Transaction.objects.bulk_create(
                        transactions,
                        batch_size=1000
                    )

                transactions.clear()

                self.stdout.write(
                    f"Generated "
                    f"{i + 1:,}/"
                    f"{count:,}"
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
        # FINAL VERIFICATION
        # --------------------------------------------------

        actual_transactions = (
            Transaction.objects.count()
        )

        actual_anomalies = (
            Transaction.objects.filter(
                is_anomaly=1
            ).count()
        )

        # --------------------------------------------------
        # RESULT
        # --------------------------------------------------

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully generated "
                f"{count:,} transactions!"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Generated anomalies: "
                f"{generated_anomalies:,}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Database transactions: "
                f"{actual_transactions:,}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Database anomalies: "
                f"{actual_anomalies:,}"
            )
        )

        if (
            generated_anomalies !=
            anomaly_target
        ):

            self.stdout.write(
                self.style.ERROR(
                    "Generated anomaly count "
                    "does not match target."
                )
            )

        elif actual_anomalies < anomaly_target:

            self.stdout.write(
                self.style.ERROR(
                    "Database already contained "
                    "anomalies, so the final anomaly "
                    "count is higher than expected."
                )
            )