from django.core.management.base import BaseCommand, CommandError
from django.db import transaction as db_transaction
from django.utils import timezone

from faker import Faker
from decimal import Decimal
from datetime import datetime
import random

from finance.models import (
    Role,
    Branch,
    User,
    Account,
    Transaction,
)


class Command(BaseCommand):
    help = "Bootstrap reproducible demo banking data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--seed",
            type=int,
            default=42,
            help="Random seed for reproducible data",
        )

        parser.add_argument(
            "--transactions",
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

    def handle(self, *args, **options):

        seed = options["seed"]
        transaction_count = options["transactions"]
        anomaly_count = options["anomalies"]

        # ============================================================
        # VALIDATION
        # ============================================================

        if transaction_count <= 0:
            raise CommandError(
                "--transactions must be greater than 0."
            )

        if anomaly_count < 0:
            raise CommandError(
                "--anomalies cannot be negative."
            )

        if anomaly_count > transaction_count:
            raise CommandError(
                "--anomalies cannot be greater than "
                "--transactions."
            )

        # ============================================================
        # REPRODUCIBILITY
        # ============================================================

        random.seed(seed)
        Faker.seed(seed)

        fake = Faker()

        self.stdout.write(
            self.style.NOTICE(
                f"Using seed={seed}"
            )
        )

        # ============================================================
        # CHECK DATABASE IS EMPTY
        # ============================================================

        existing_transactions = Transaction.objects.count()
        existing_accounts = Account.objects.count()
        existing_users = User.objects.count()
        existing_branches = Branch.objects.count()
        existing_roles = Role.objects.count()

        if any(
            [
                existing_transactions,
                existing_accounts,
                existing_users,
                existing_branches,
                existing_roles,
            ]
        ):
            raise CommandError(
                "Database is not empty. "
                "bootstrap_demo_data must be run against "
                "an empty finance database."
            )

        # ============================================================
        # DATABASE TRANSACTION
        # ============================================================

        with db_transaction.atomic():

            # ========================================================
            # ROLES
            # ========================================================

            self.stdout.write("Creating roles...")

            roles = [
                Role(role_name="Admin"),
                Role(role_name="Manager"),
                Role(role_name="Customer"),
            ]

            Role.objects.bulk_create(
                roles,
                batch_size=100,
            )

            customer_role = Role.objects.get(
                role_name="Customer"
            )

            # ========================================================
            # BRANCHES
            # ========================================================

            self.stdout.write("Creating branches...")

            branch_data = [
                {
                    "branch_name": "Kannur",
                    "city": "Kannur",
                    "state": "Kerala",
                    "ifsc_code": "FINB0000001",
                    "phone": "04972700001",
                },
                {
                    "branch_name": "Kochi",
                    "city": "Kochi",
                    "state": "Kerala",
                    "ifsc_code": "FINB0000002",
                    "phone": "04842700002",
                },
                {
                    "branch_name": "Calicut",
                    "city": "Kozhikode",
                    "state": "Kerala",
                    "ifsc_code": "FINB0000003",
                    "phone": "04952700003",
                },
                {
                    "branch_name": "Trivandrum",
                    "city": "Thiruvananthapuram",
                    "state": "Kerala",
                    "ifsc_code": "FINB0000004",
                    "phone": "04712700004",
                },
                {
                    "branch_name": "Bangalore",
                    "city": "Bangalore",
                    "state": "Karnataka",
                    "ifsc_code": "FINB0000005",
                    "phone": "08027000005",
                },
            ]

            branches = [
                Branch(**data)
                for data in branch_data
            ]

            Branch.objects.bulk_create(
                branches,
                batch_size=100,
            )

            branches = list(
                Branch.objects.order_by("branch_id")
            )

            # ========================================================
            # USERS
            # ========================================================

            self.stdout.write(
                "Creating 500 users..."
            )

            users = []

            for i in range(500):

                branch = branches[
                    i % len(branches)
                ]

                user = User(
                    username=f"user_{i + 1:04d}",
                    email=(
                        f"user{i + 1:04d}"
                        "@example.com"
                    ),
                    role=customer_role,
                    branch=branch,
                )

                # IMPORTANT:
                # Store a properly hashed password.
                # Never manually store password hashes.
                user.set_password("Password@123")

                users.append(user)

            User.objects.bulk_create(
                users,
                batch_size=500,
            )

            users = list(
                User.objects.order_by("user_id")
            )

            # ========================================================
            # ACCOUNTS
            # ========================================================

            self.stdout.write(
                "Creating 1000 accounts..."
            )

            accounts = []

            for i in range(1000):

                user = users[
                    i % len(users)
                ]

                account_type = (
                    "Savings"
                    if i % 2 == 0
                    else "Current"
                )

                accounts.append(
                    Account(
                        user=user,
                        account_number=(
                            f"ACC{i + 1:09d}"
                        ),
                        account_type=account_type,
                        balance=Decimal(
                            str(
                                round(
                                    random.uniform(
                                        5000,
                                        500000,
                                    ),
                                    2,
                                )
                            )
                        ),
                        created_at=timezone.now(),
                    )
                )

            Account.objects.bulk_create(
                accounts,
                batch_size=500,
            )

            accounts = list(
                Account.objects.order_by(
                    "account_id"
                )
            )

            # ========================================================
            # TRANSACTIONS
            # ========================================================

            self.stdout.write(
                f"Creating "
                f"{transaction_count:,} transactions..."
            )

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

            start_date = datetime(
                2024,
                1,
                1,
            )

            end_date = datetime(
                2025,
                12,
                31,
                23,
                59,
                59,
            )

            # ========================================================
            # EXACT ANOMALY POSITIONS
            # ========================================================

            anomaly_indices = set(
                random.sample(
                    range(transaction_count),
                    anomaly_count,
                )
            )

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
            }

            transactions = []
            generated_anomalies = 0

            # ========================================================
            # GENERATE TRANSACTIONS
            # ========================================================

            for i in range(transaction_count):

                account = random.choice(accounts)

                # ----------------------------------------------------
                # TRANSACTION DATE
                # ----------------------------------------------------

                transaction_time = timezone.make_aware(
                    fake.date_time_between(
                        start_date=start_date,
                        end_date=end_date,
                    )
                )

                month = transaction_time.month

                # ----------------------------------------------------
                # SEASONAL AMOUNT
                # ----------------------------------------------------

                base_amount = random.uniform(
                    500,
                    75000,
                )

                amount = (
                    base_amount
                    * seasonal_factor.get(
                        month,
                        1.0,
                    )
                )

                amount *= random.uniform(
                    0.85,
                    1.15,
                )

                # ----------------------------------------------------
                # TRANSACTION TYPE
                # ----------------------------------------------------

                transaction_type = random.choice(
                    transaction_types
                )

                # ----------------------------------------------------
                # ANOMALY GENERATION
                # ----------------------------------------------------

                is_anomaly = 0

                if i in anomaly_indices:

                    is_anomaly = 1
                    generated_anomalies += 1

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
                            15,
                        )

                    elif anomaly_type == "unusual_amount":

                        amount = random.uniform(
                            150000,
                            500000,
                        )

                    else:

                        transaction_type = random.choice(
                            [
                                "Transfer",
                                "Withdrawal",
                            ]
                        )

                        amount *= random.uniform(
                            3,
                            10,
                        )

                # ----------------------------------------------------
                # CREATE TRANSACTION OBJECT
                # ----------------------------------------------------

                transactions.append(
                    Transaction(
                        account=account,
                        amount=Decimal(
                            str(
                                round(
                                    amount,
                                    2,
                                )
                            )
                        ),
                        transaction_type=(
                            transaction_type
                        ),
                        merchant=fake.company(),
                        location=fake.city(),
                        transaction_time=(
                            transaction_time
                        ),
                        status=random.choice(
                            statuses
                        ),
                        is_anomaly=is_anomaly,
                    )
                )

                # ----------------------------------------------------
                # BULK INSERT EVERY 1000 RECORDS
                # ----------------------------------------------------

                if len(transactions) >= 1000:

                    Transaction.objects.bulk_create(
                        transactions,
                        batch_size=1000,
                    )

                    transactions.clear()

                    self.stdout.write(
                        f"Generated "
                        f"{i + 1:,}/"
                        f"{transaction_count:,}"
                    )

            # ========================================================
            # INSERT REMAINING TRANSACTIONS
            # ========================================================

            if transactions:

                Transaction.objects.bulk_create(
                    transactions,
                    batch_size=1000,
                )

            # ========================================================
            # VERIFY GENERATED DATA
            # ========================================================

            actual_users = User.objects.count()

            actual_accounts = Account.objects.count()

            actual_transactions = (
                Transaction.objects.count()
            )

            actual_anomalies = (
                Transaction.objects.filter(
                    is_anomaly=1
                ).count()
            )

            # ========================================================
            # VALIDATION
            # ========================================================

            if actual_users != 500:

                raise CommandError(
                    "User count verification failed. "
                    f"Expected 500, got {actual_users}."
                )

            if actual_accounts != 1000:

                raise CommandError(
                    "Account count verification failed. "
                    f"Expected 1000, got "
                    f"{actual_accounts}."
                )

            if actual_transactions != transaction_count:

                raise CommandError(
                    "Transaction count verification failed. "
                    f"Expected {transaction_count}, "
                    f"got {actual_transactions}."
                )

            if actual_anomalies != anomaly_count:

                raise CommandError(
                    "Anomaly count verification failed. "
                    f"Expected {anomaly_count}, "
                    f"got {actual_anomalies}."
                )

            if generated_anomalies != anomaly_count:

                raise CommandError(
                    "Generated anomaly count verification "
                    "failed. "
                    f"Expected {anomaly_count}, "
                    f"generated {generated_anomalies}."
                )

        # ============================================================
        # FINAL SUCCESS MESSAGE
        # ============================================================

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "========================================"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Demo data bootstrap completed"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "========================================"
            )
        )

        self.stdout.write(
            f"Roles:        {Role.objects.count()}"
        )

        self.stdout.write(
            f"Branches:     {Branch.objects.count()}"
        )

        self.stdout.write(
            f"Users:        {actual_users}"
        )

        self.stdout.write(
            f"Accounts:     {actual_accounts}"
        )

        self.stdout.write(
            f"Transactions: {actual_transactions:,}"
        )

        self.stdout.write(
            f"Anomalies:    {actual_anomalies:,}"
        )

        self.stdout.write(
            self.style.SUCCESS(
                "All requested data verified successfully."
            )
        )