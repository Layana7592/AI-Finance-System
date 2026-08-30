from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from faker import Faker

from finance.models import User, Role, Branch


fake = Faker()


class Command(BaseCommand):
    help = "Generate fake users with default roles and branches"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=100,
            help="Number of users to generate"
        )

    def create_default_roles(self):
        roles = [
            "Admin",
            "Manager",
            "Staff",
            "Customer",
        ]

        created_roles = []

        for role_name in roles:
            role, created = Role.objects.get_or_create(
                role_name=role_name
            )

            if created:
                created_roles.append(role_name)

        if created_roles:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created roles: {', '.join(created_roles)}"
                )
            )
        else:
            self.stdout.write(
                "All required roles already exist."
            )

    def create_default_branches(self):
        branches = [
            {
                "branch_name": "Kannur Branch",
                "city": "Kannur",
                "state": "Kerala",
                "ifsc_code": "AIFS0000001",
                "phone": "9876500001",
            },
            {
                "branch_name": "Kochi Branch",
                "city": "Kochi",
                "state": "Kerala",
                "ifsc_code": "AIFS0000002",
                "phone": "9876500002",
            },
            {
                "branch_name": "Calicut Branch",
                "city": "Calicut",
                "state": "Kerala",
                "ifsc_code": "AIFS0000003",
                "phone": "9876500003",
            },
            {
                "branch_name": "Trivandrum Branch",
                "city": "Trivandrum",
                "state": "Kerala",
                "ifsc_code": "AIFS0000004",
                "phone": "9876500004",
            },
            {
                "branch_name": "Bangalore Branch",
                "city": "Bangalore",
                "state": "Karnataka",
                "ifsc_code": "AIFS0000005",
                "phone": "9876500005",
            },
        ]

        created_branches = []

        for branch_data in branches:
            branch, created = Branch.objects.get_or_create(
                branch_name=branch_data["branch_name"],
                defaults={
                    "city": branch_data["city"],
                    "state": branch_data["state"],
                    "ifsc_code": branch_data["ifsc_code"],
                    "phone": branch_data["phone"],
                }
            )

            if created:
                created_branches.append(branch.branch_name)

        if created_branches:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created branches: {', '.join(created_branches)}"
                )
            )
        else:
            self.stdout.write(
                "All required branches already exist."
            )

    def handle(self, *args, **options):
        count = options["count"]

        if count <= 0:
            self.stdout.write(
                self.style.ERROR(
                    "User count must be greater than 0."
                )
            )
            return

        # --------------------------------------------------------
        # STEP 1: Create required roles
        # --------------------------------------------------------

        self.stdout.write(
            self.style.WARNING(
                "Checking required roles..."
            )
        )

        self.create_default_roles()

        # --------------------------------------------------------
        # STEP 2: Create required branches
        # --------------------------------------------------------

        self.stdout.write(
            self.style.WARNING(
                "Checking required branches..."
            )
        )

        self.create_default_branches()

        # --------------------------------------------------------
        # STEP 3: Get roles and branches
        # --------------------------------------------------------

        roles = list(Role.objects.all())
        branches = list(Branch.objects.all())

        if not roles:
            self.stdout.write(
                self.style.ERROR(
                    "Unable to find or create roles."
                )
            )
            return

        if not branches:
            self.stdout.write(
                self.style.ERROR(
                    "Unable to find or create branches."
                )
            )
            return

        # --------------------------------------------------------
        # STEP 4: Generate users
        # --------------------------------------------------------

        self.stdout.write(
            f"Generating {count} users..."
        )

        users = []

        for _ in range(count):
            users.append(
                User(
                    username=fake.unique.user_name(),
                    email=fake.unique.email(),
                    password_hash=make_password("Password@123"),
                    role=fake.random_element(roles),
                    branch=fake.random_element(branches),
                    created_at=timezone.now(),
                )
            )

        User.objects.bulk_create(users)

        # --------------------------------------------------------
        # STEP 5: Success message
        # --------------------------------------------------------

        self.stdout.write(
            self.style.SUCCESS(
                f"{count} users generated successfully!"
            )
        )

        self.stdout.write(
            f"Total roles: {Role.objects.count()}"
        )

        self.stdout.write(
            f"Total branches: {Branch.objects.count()}"
        )

        self.stdout.write(
            f"Total users: {User.objects.count()}"
        )