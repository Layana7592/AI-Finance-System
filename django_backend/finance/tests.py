
from django.utils import timezone
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from .models import (
    Role,
    Branch,
    User,
    Account,
    Transaction,
)


class ModelSetupTests(TestCase):
    """Tests for the basic banking model relationships."""

    def setUp(self):
        self.role = Role.objects.create(
            role_name="Test Role"
        )

        self.branch = Branch.objects.create(
            branch_name="Test Branch",
            city="Kannur",
            state="Kerala",
            ifsc_code="TEST000001",
            phone="9876543210",
        )

        self.user = User.objects.create(
            username="testuser",
            email="test@example.com",
            password_hash="test-password",
            created_at=timezone.now(),
            role=self.role,
            branch=self.branch,
        )

    def test_role_created(self):
        """Role can be created successfully."""
        self.assertEqual(Role.objects.count(), 1)
        self.assertEqual(self.role.role_name, "Test Role")

    def test_branch_created(self):
        """Branch can be created successfully."""
        self.assertEqual(Branch.objects.count(), 1)
        self.assertEqual(self.branch.branch_name, "Test Branch")

    def test_user_linked_to_role_and_branch(self):
        """User is correctly linked to Role and Branch."""
        self.assertEqual(self.user.role, self.role)
        self.assertEqual(self.user.branch, self.branch)

    def test_account_linked_to_user(self):
        """Account is correctly linked to a user."""
        account = Account.objects.create(
            account_number="TESTACC001",
            account_type="Savings",
            balance=Decimal("50000.00"),
            created_at=timezone.now(),
            user=self.user,
        )

        self.assertEqual(account.user, self.user)
        self.assertEqual(account.account_number, "TESTACC001")


class TransactionAPITests(TestCase):
    """Tests for the Transactions API."""

    def setUp(self):
        self.client = APIClient()

        self.role = Role.objects.create(
            role_name="Transaction Test Role"
        )

        self.branch = Branch.objects.create(
            branch_name="Transaction Test Branch",
            city="Kannur",
            state="Kerala",
            ifsc_code="TEST000002",
            phone="9876543211",
        )

        self.user = User.objects.create(
            username="transactionuser",
            email="transaction@example.com",
            password_hash="test-password",
            created_at=timezone.now(),
            role=self.role,
            branch=self.branch,
        )

        self.account = Account.objects.create(
            account_number="TESTACC002",
            account_type="Savings",
            balance=Decimal("10000.00"),
            created_at=timezone.now(),
            user=self.user,
        )

        self.transaction = Transaction.objects.create(
            account=self.account,
            amount=Decimal("500.00"),
            transaction_type="Credit",
            merchant="Test Merchant",
            location="Kannur",
            transaction_time=timezone.now(),
            status="Completed",
            is_anomaly=0,
        )

    def test_transaction_exists(self):
        """Transaction is created successfully."""
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(
            self.transaction.amount,
            Decimal("500.00")
        )

    def test_transaction_list_api(self):
        """GET /api/transactions/ returns transactions."""
        response = self.client.get("/api/transactions/")

        self.assertEqual(response.status_code, 200)

        # DRF may return either a list or paginated response.
        if isinstance(response.data, dict):
            self.assertIn("results", response.data)
            transactions = response.data["results"]
        else:
            transactions = response.data

        self.assertGreaterEqual(len(transactions), 1)


class UserAPITests(TestCase):
    """Tests for the Users API."""

    def setUp(self):
        self.client = APIClient()

        self.role = Role.objects.create(
            role_name="API Test Role"
        )

        self.branch = Branch.objects.create(
            branch_name="API Test Branch",
            city="Kochi",
            state="Kerala",
            ifsc_code="TEST000003",
            phone="9876543212",
        )

        self.user = User.objects.create(
            username="apiuser",
            email="api@example.com",
            password_hash="test-password",
            created_at=timezone.now(),
            role=self.role,
            branch=self.branch,
        )

    def test_user_list_api(self):
        """GET /api/users/ returns users."""
        response = self.client.get("/api/users/")

        self.assertEqual(response.status_code, 200)

        if isinstance(response.data, dict):
            self.assertIn("results", response.data)
            users = response.data["results"]
        else:
            users = response.data

        self.assertGreaterEqual(len(users), 1)


class AccountAPITests(TestCase):
    """Tests for the Accounts API."""

    def setUp(self):
        self.client = APIClient()

        self.role = Role.objects.create(
            role_name="Account Test Role"
        )

        self.branch = Branch.objects.create(
            branch_name="Account Test Branch",
            city="Calicut",
            state="Kerala",
            ifsc_code="TEST000004",
            phone="9876543213",
        )

        self.user = User.objects.create(
            username="accountuser",
            email="account@example.com",
            password_hash="test-password",
            created_at=timezone.now(),
            role=self.role,
            branch=self.branch,
        )

        self.account = Account.objects.create(
            account_number="TESTACC003",
            account_type="Current",
            balance=Decimal("25000.00"),
            created_at=timezone.now(),
            user=self.user,
        )

    def test_account_list_api(self):
        """GET /api/accounts/ returns accounts."""
        response = self.client.get("/api/accounts/")

        self.assertEqual(response.status_code, 200)

        if isinstance(response.data, dict):
            self.assertIn("results", response.data)
            accounts = response.data["results"]
        else:
            accounts = response.data

        self.assertGreaterEqual(len(accounts), 1)

