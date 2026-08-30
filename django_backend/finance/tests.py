<<<<<<< ours
from decimal import Decimal

from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from django.utils import timezone

=======

from django.utils import timezone
from decimal import Decimal

from django.test import TestCase
>>>>>>> theirs
from rest_framework.test import APIClient

from .models import (
    Role,
    Branch,
    User,
    Account,
    Transaction,
<<<<<<< ours
    FinancialForecast,
)


# ============================================================
# BASIC MODEL TESTS
# ============================================================

=======
)


>>>>>>> theirs
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

<<<<<<< ours
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="test-password",
=======
        self.user = User.objects.create(
            username="testuser",
            email="test@example.com",
            password_hash="test-password",
            created_at=timezone.now(),
>>>>>>> theirs
            role=self.role,
            branch=self.branch,
        )

    def test_role_created(self):
<<<<<<< ours
=======
        """Role can be created successfully."""
>>>>>>> theirs
        self.assertEqual(Role.objects.count(), 1)
        self.assertEqual(self.role.role_name, "Test Role")

    def test_branch_created(self):
<<<<<<< ours
=======
        """Branch can be created successfully."""
>>>>>>> theirs
        self.assertEqual(Branch.objects.count(), 1)
        self.assertEqual(self.branch.branch_name, "Test Branch")

    def test_user_linked_to_role_and_branch(self):
<<<<<<< ours
=======
        """User is correctly linked to Role and Branch."""
>>>>>>> theirs
        self.assertEqual(self.user.role, self.role)
        self.assertEqual(self.user.branch, self.branch)

    def test_account_linked_to_user(self):
<<<<<<< ours
=======
        """Account is correctly linked to a user."""
>>>>>>> theirs
        account = Account.objects.create(
            account_number="TESTACC001",
            account_type="Savings",
            balance=Decimal("50000.00"),
            created_at=timezone.now(),
            user=self.user,
        )

        self.assertEqual(account.user, self.user)
        self.assertEqual(account.account_number, "TESTACC001")


<<<<<<< ours
# ============================================================
# TRANSACTION API TESTS
# ============================================================

=======
>>>>>>> theirs
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

<<<<<<< ours
        self.user = User.objects.create_user(
            username="transactionuser",
            email="transaction@example.com",
            password="test-password",
=======
        self.user = User.objects.create(
            username="transactionuser",
            email="transaction@example.com",
            password_hash="test-password",
            created_at=timezone.now(),
>>>>>>> theirs
            role=self.role,
            branch=self.branch,
        )

<<<<<<< ours
        # Authenticate API test client
        self.client.force_authenticate(
            user=self.user
        )

=======
>>>>>>> theirs
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
<<<<<<< ours
        self.assertEqual(
            Transaction.objects.count(),
            1
        )

=======
        """Transaction is created successfully."""
        self.assertEqual(Transaction.objects.count(), 1)
>>>>>>> theirs
        self.assertEqual(
            self.transaction.amount,
            Decimal("500.00")
        )

    def test_transaction_list_api(self):
<<<<<<< ours
        response = self.client.get(
            "/api/transactions/"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        if isinstance(response.data, dict):
            self.assertIn(
                "results",
                response.data
            )
=======
        """GET /api/transactions/ returns transactions."""
        response = self.client.get("/api/transactions/")

        self.assertEqual(response.status_code, 200)

        # DRF may return either a list or paginated response.
        if isinstance(response.data, dict):
            self.assertIn("results", response.data)
>>>>>>> theirs
            transactions = response.data["results"]
        else:
            transactions = response.data

<<<<<<< ours
        self.assertGreaterEqual(
            len(transactions),
            1
        )


# ============================================================
# USER API TESTS
# ============================================================
=======
        self.assertGreaterEqual(len(transactions), 1)

>>>>>>> theirs

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

<<<<<<< ours
        self.user = User.objects.create_user(
            username="apiuser",
            email="api@example.com",
            password="test-password",
=======
        self.user = User.objects.create(
            username="apiuser",
            email="api@example.com",
            password_hash="test-password",
            created_at=timezone.now(),
>>>>>>> theirs
            role=self.role,
            branch=self.branch,
        )

<<<<<<< ours
        # Authenticate API test client
        self.client.force_authenticate(
            user=self.user
        )

    def test_user_list_api(self):
        response = self.client.get(
            "/api/users/"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        if isinstance(response.data, dict):
            self.assertIn(
                "results",
                response.data
            )
=======
    def test_user_list_api(self):
        """GET /api/users/ returns users."""
        response = self.client.get("/api/users/")

        self.assertEqual(response.status_code, 200)

        if isinstance(response.data, dict):
            self.assertIn("results", response.data)
>>>>>>> theirs
            users = response.data["results"]
        else:
            users = response.data

<<<<<<< ours
        self.assertGreaterEqual(
            len(users),
            1
        )

    def test_password_hash_never_returned(self):
        """Password hashes must never be exposed through the API."""

        response = self.client.get(
            "/api/users/"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        if isinstance(response.data, dict):
            users = response.data.get(
                "results",
                []
            )
        else:
            users = response.data

        self.assertGreaterEqual(
            len(users),
            1
        )

        for user_data in users:
            self.assertNotIn(
                "password_hash",
                user_data
            )

            self.assertNotIn(
                "password",
                user_data
            )


# ============================================================
# ACCOUNT API TESTS
# ============================================================
=======
        self.assertGreaterEqual(len(users), 1)

>>>>>>> theirs

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

<<<<<<< ours
        self.user = User.objects.create_user(
            username="accountuser",
            email="account@example.com",
            password="test-password",
=======
        self.user = User.objects.create(
            username="accountuser",
            email="account@example.com",
            password_hash="test-password",
            created_at=timezone.now(),
>>>>>>> theirs
            role=self.role,
            branch=self.branch,
        )

<<<<<<< ours
        # Authenticate API test client
        self.client.force_authenticate(
            user=self.user
        )

=======
>>>>>>> theirs
        self.account = Account.objects.create(
            account_number="TESTACC003",
            account_type="Current",
            balance=Decimal("25000.00"),
            created_at=timezone.now(),
            user=self.user,
        )

    def test_account_list_api(self):
<<<<<<< ours
        response = self.client.get(
            "/api/accounts/"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        if isinstance(response.data, dict):
            self.assertIn(
                "results",
                response.data
            )
=======
        """GET /api/accounts/ returns accounts."""
        response = self.client.get("/api/accounts/")

        self.assertEqual(response.status_code, 200)

        if isinstance(response.data, dict):
            self.assertIn("results", response.data)
>>>>>>> theirs
            accounts = response.data["results"]
        else:
            accounts = response.data

<<<<<<< ours
        self.assertGreaterEqual(
            len(accounts),
            1
        )


# ============================================================
# MIGRATION TESTS
# ============================================================

class MigrationTests(TestCase):
    """Verify the current PostgreSQL migration state."""

    def test_migrations_are_applied(self):
        self.assertEqual(
            connection.vendor,
            "postgresql"
        )

        call_command(
            "migrate",
            verbosity=0,
            interactive=False,
        )

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM django_migrations
                WHERE app = 'finance'
                """
            )

            applied_count = cursor.fetchone()[0]

        self.assertGreaterEqual(
            applied_count,
            3
        )

    def test_transactions_anomaly_column_is_smallint(self):
        """is_anomaly must match the Django SmallIntegerField."""

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT data_type
                FROM information_schema.columns
                WHERE table_name = 'transactions'
                AND column_name = 'is_anomaly'
                """
            )

            result = cursor.fetchone()

        self.assertIsNotNone(
            result
        )

        self.assertEqual(
            result[0],
            "smallint"
        )


# ============================================================
# DEMO DATA TESTS
# ============================================================

class DemoDataTests(TestCase):
    """
    Tests the reproducible demo-data bootstrap command.
    """

    @classmethod
    def setUpTestData(cls):
        call_command(
            "bootstrap_demo_data",
            seed=42,
            transactions=50000,
            anomalies=500,
            verbosity=0,
        )

    def test_expected_entity_counts(self):
        """Verify all expected demo-data counts."""

        self.assertEqual(
            Role.objects.count(),
            3
        )

        self.assertEqual(
            Branch.objects.count(),
            5
        )

        self.assertEqual(
            User.objects.count(),
            500
        )

        self.assertEqual(
            Account.objects.count(),
            1000
        )

        self.assertEqual(
            Transaction.objects.count(),
            50000
        )

    def test_users_cover_multiple_branches(self):
        """Users must belong to multiple branches."""

        branch_count = (
            User.objects
            .values("branch_id")
            .distinct()
            .count()
        )

        self.assertGreaterEqual(
            branch_count,
            3
        )

    def test_transactions_cover_multiple_branches(self):
        """Transactions must cover multiple branches."""

        branch_count = (
            Transaction.objects
            .values("account__user__branch_id")
            .distinct()
            .count()
        )

        self.assertGreaterEqual(
            branch_count,
            3
        )

    def test_exactly_500_anomaly_labels(self):
        """Exactly 500 transactions must be labelled anomalous."""

        anomaly_count = (
            Transaction.objects
            .filter(is_anomaly=1)
            .count()
        )

        self.assertEqual(
            anomaly_count,
            500
        )


# ============================================================
# CORE API TESTS
# ============================================================

class CoreAPITests(TestCase):
    """Verify the core API endpoints."""

    def setUp(self):
        self.client = APIClient()

        role = Role.objects.create(
            role_name="Core API Role"
        )

        branch = Branch.objects.create(
            branch_name="Core API Branch",
            city="Kannur",
            state="Kerala",
            ifsc_code="TEST000005",
            phone="9876543214",
        )

        user = User.objects.create_user(
            username="coreapiuser",
            email="coreapi@example.com",
            password="test-password",
            role=role,
            branch=branch,
        )

        # Authenticate API test client
        self.client.force_authenticate(
            user=user
        )

        Account.objects.create(
            account_number="TESTACC004",
            account_type="Savings",
            balance=Decimal("50000.00"),
            created_at=timezone.now(),
            user=user,
        )

    def test_core_api_endpoints(self):
        endpoints = [
            "/api/users/",
            "/api/accounts/",
            "/api/transactions/",
            "/api/fraud-predictions/",
            "/api/forecasts/",
            "/api/audit-logs/",
            "/api/alerts/",
            "/api/journal-entries/",
        ]

        for endpoint in endpoints:

            with self.subTest(
                endpoint=endpoint
            ):
                response = self.client.get(
                    endpoint
                )

                self.assertEqual(
                    response.status_code,
                    200,
                    f"{endpoint} returned "
                    f"{response.status_code}"
                )


# ============================================================
# FORECAST TESTS
# ============================================================

class ForecastGenerationTests(TestCase):
    """Verify that forecast generation creates 12 rows."""

    @classmethod
    def setUpTestData(cls):

        role = Role.objects.create(
            role_name="Forecast Test Role"
        )

        branch = Branch.objects.create(
            branch_name="Forecast Test Branch",
            city="Kannur",
            state="Kerala",
            ifsc_code="TEST000006",
            phone="9876543215",
        )

        user = User.objects.create_user(
            username="forecastuser",
            email="forecast@example.com",
            password="test-password",
            role=role,
            branch=branch,
        )

        account = Account.objects.create(
            account_number="TESTACC005",
            account_type="Savings",
            balance=Decimal("100000.00"),
            created_at=timezone.now(),
            user=user,
        )

        # Create 24 months of historical data.
        for month_index in range(24):

            year = 2024 + (
                month_index // 12
            )

            month = (
                month_index % 12
            ) + 1

            transaction_time = (
                timezone.make_aware(
                    timezone.datetime(
                        year,
                        month,
                        15,
                        12,
                        0,
                        0,
                    )
                )
            )

            # Income
            Transaction.objects.create(
                account=account,
                amount=Decimal(
                    str(
                        10000
                        + month_index * 250
                    )
                ),
                transaction_type="Deposit",
                merchant="Forecast Income",
                location="Kannur",
                transaction_time=transaction_time,
                status="Completed",
                is_anomaly=0,
            )

            # Expense
            Transaction.objects.create(
                account=account,
                amount=Decimal(
                    str(
                        5000
                        + month_index * 100
                    )
                ),
                transaction_type="Payment",
                merchant="Forecast Expense",
                location="Kannur",
                transaction_time=transaction_time,
                status="Completed",
                is_anomaly=0,
            )

    def test_forecast_generation_creates_12_rows(self):
        """POST /api/forecasts/generate/ creates 12 forecasts."""

        client = APIClient()

        # Authenticate the forecast API request.
        user = User.objects.get(
            username="forecastuser"
        )

        client.force_authenticate(
            user=user
        )

        response = client.post(
            "/api/forecasts/generate/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
            f"Forecast API returned "
            f"{response.status_code}: "
            f"{response.data}"
        )

        self.assertEqual(
            FinancialForecast.objects.count(),
            12
        )

        self.assertEqual(
            FinancialForecast.objects
            .values("forecast_month")
            .distinct()
            .count(),
            12
        )
=======
        self.assertGreaterEqual(len(accounts), 1)

>>>>>>> theirs
