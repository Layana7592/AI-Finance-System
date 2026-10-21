"""Create a dedicated, nonproduction presenter identity and synthetic history.

After `bootstrap_demo_data`:
    DEMO_PRESENTER_PASSWORD='<private-password>' python manage.py prepare_demo_presenter

Never hardcode or commit a presenter password.
"""
import os
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction as db_transaction
from django.utils import timezone

from finance.models import Account, Branch, Role, Transaction, User


class Command(BaseCommand):
    help = "Create or reset a synthetic presenter user and account for an isolated viva demo"

    def handle(self, *args, **kwargs):
        password = os.getenv("DEMO_PRESENTER_PASSWORD", "")
        if len(password) < 12:
            raise CommandError(
                "Provide DEMO_PRESENTER_PASSWORD (12+ characters) in your shell, "
                "not in Git. This command is for synthetic demo databases only."
            )
        role = Role.objects.filter(role_name="Admin").first()
        branch = Branch.objects.order_by("branch_id").first()
        if role is None or branch is None:
            raise CommandError("Run bootstrap_demo_data first.")
        now = timezone.now()

        with db_transaction.atomic():
            user, _ = User.objects.get_or_create(
                username="demo_presenter",
                defaults={
                    "email": "demo_presenter@example.invalid",
                    "role": role,
                    "branch": branch,
                },
            )
            user.role = role
            user.branch = branch
            user.set_password(password)
            user.save(update_fields=["role", "branch", "password"])

            account, _ = Account.objects.get_or_create(
                account_number="DEMO-ACCOUNT-2026",
                defaults={
                    "user": user, "account_type": "Savings",
                    "balance": Decimal("50000.00"), "created_at": now,
                },
            )
            if account.user_id != user.pk:
                raise CommandError("The demonstration account belongs to another user.")

            # Preserve any transaction created during earlier presentation.
            # Install the stable baseline only when this account is new.
            if not Transaction.objects.filter(account=account).exists():
                baseline = [
                    Transaction(
                        account=account,
                        amount=Decimal(str(90 + (i % 6) * 4)),
                        transaction_type="Purchase",
                        merchant="RegularMarket",
                        location="Kochi",
                        transaction_time=(now - timedelta(days=20-i)).replace(
                            hour=10, minute=0, second=0, microsecond=0
                        ),
                        status="Completed",
                        is_anomaly=0,
                    )
                    for i in range(12)
                ]
                Transaction.objects.bulk_create(baseline)

        self.stdout.write(self.style.SUCCESS(
            "Presenter prepared: username=demo_presenter, "
            "account=DEMO-ACCOUNT-2026; password was not printed."
        ))
