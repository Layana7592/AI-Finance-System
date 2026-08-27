from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker
from decimal import Decimal
import random

from finance.models import Account, User


class Command(BaseCommand):
    help = "Generate fake accounts for existing users"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=10,
            help="Number of accounts to generate",
        )

    def handle(self, *args, **options):
        fake = Faker()
        count = options["count"]

        if count <= 0:
            self.stdout.write(
                self.style.ERROR(
                    "Account count must be greater than 0."
                )
            )
            return

        users = list(User.objects.all())

        if not users:
            self.stdout.write(
                self.style.ERROR(
                    "No users found. Generate users first."
                )
            )
            return

        account_types = [
            "Savings",
            "Current",
            "Salary",
        ]

        accounts = []

        for _ in range(count):
            user = random.choice(users)

            accounts.append(
                Account(
                    user=user,
                    account_number=fake.unique.numerify(
                        text="################"
                    ),
                    account_type=random.choice(account_types),
                    balance=Decimal(
                        str(round(random.uniform(1000, 500000), 2))
                    ),
                    created_at=timezone.now(),
                )
            )

        Account.objects.bulk_create(accounts)

        self.stdout.write(
            self.style.SUCCESS(
                f"{count} accounts generated successfully!"
            )
        )

        self.stdout.write(
            f"Total users: {User.objects.count()}"
        )

        self.stdout.write(
            f"Total accounts: {Account.objects.count()}"
        )