from django.core.management.base import BaseCommand
from django.db import IntegrityError
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

        generated = 0

        for _ in range(count):
            user = random.choice(users)

            account = Account(
                user=user,
                account_number=fake.unique.numerify(
                    text="################"
                ),
                account_type=random.choice(account_types),
                balance=Decimal(
                    str(round(random.uniform(1000, 500000), 2))
                ),
            )

            try:
                account.save()
                generated += 1

            except IntegrityError:
                continue

        self.stdout.write(
            self.style.SUCCESS(
                f"{generated} accounts generated successfully!"
            )
        )