from django.core.management.base import BaseCommand
from django.db import IntegrityError
from faker import Faker
from decimal import Decimal
import random

from finance.models import Transaction, Account


class Command(BaseCommand):
    help = "Generate fake financial transactions"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=100,
            help="Number of transactions to generate",
        )

    def handle(self, *args, **options):
        fake = Faker()
        count = options["count"]

        # Get existing accounts
        accounts = list(Account.objects.all())

        if not accounts:
            self.stdout.write(
                self.style.ERROR(
                    "No accounts found. Generate accounts first."
                )
            )
            return

        transaction_types = [
            "Deposit",
            "Withdrawal",
            "Transfer",
            "Payment",
            "Purchase",
        ]

        statuses = [
            "Completed",
            "Pending",
            "Failed",
        ]

        generated = 0

        for _ in range(count):
            account = random.choice(accounts)

            transaction = Transaction(
                account=account,
                amount=Decimal(
                    str(round(random.uniform(100, 100000), 2))
                ),
                transaction_type=random.choice(transaction_types),
                merchant=fake.company(),
                location=fake.city(),
                transaction_time=fake.date_time_between(
                    start_date="-730d",
                    end_date="now"
                ),
                status=random.choice(statuses),
            )

            try:
                transaction.save()
                generated += 1

            except IntegrityError:
                continue

        self.stdout.write(
            self.style.SUCCESS(
                f"{generated} transactions generated successfully!"
            )
        )