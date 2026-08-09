from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from faker import Faker

from finance.models import User, Role, Branch


fake = Faker()


class Command(BaseCommand):
    help = "Generate fake users"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=100,
            help="Number of users to generate"
        )

    def handle(self, *args, **options):
        count = options["count"]

        role = Role.objects.first()

        if not role:
            self.stdout.write(
                self.style.ERROR(
                    "No roles found. Please create roles first."
                )
            )
            return

        branch = Branch.objects.first()

        if not branch:
            self.stdout.write(
                self.style.ERROR(
                    "No branches found. Please create branches first."
                )
            )
            return

        users = []

        for _ in range(count):
            users.append(
                User(
                    username=fake.unique.user_name(),
                    email=fake.unique.email(),
                    password_hash=make_password("Password@123"),
                    role=role,
                    branch=branch,
                    created_at=timezone.now()
                )
            )

        User.objects.bulk_create(users)

        self.stdout.write(
            self.style.SUCCESS(
                f"{count} users generated successfully!"
            )
        )