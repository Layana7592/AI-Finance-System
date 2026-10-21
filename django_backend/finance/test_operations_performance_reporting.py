"""Operational access, research-cache and Gemini safety regression tests."""
from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from finance.models import (
    Account, Alert, AuditLog, Branch, Role, Transaction, User,
)
from finance.services.cached_research import (
    get_cached_research_evaluations, research_dataset_fingerprint,
)
from finance.services.gemini_service import (
    build_report_prompt, generate_gemini_report, render_verified_numeric_report,
    validate_narrative,
)


class OperationalWorkspaceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_role = Role.objects.create(role_name="Admin")
        cls.manager_role = Role.objects.create(role_name="Manager")
        cls.customer_role = Role.objects.create(role_name="Customer")
        cls.branch_a = Branch.objects.create(
            branch_name="Kochi A", city="Kochi", state="Kerala",
            ifsc_code="OPS00000001", phone="9000000001",
        )
        cls.branch_b = Branch.objects.create(
            branch_name="Kannur B", city="Kannur", state="Kerala",
            ifsc_code="OPS00000002", phone="9000000002",
        )
        cls.admin = User.objects.create_user(
            username="ops-admin", email="ops-admin@example.invalid", password="test-only", role=cls.admin_role,
            branch=cls.branch_a,
        )
        cls.manager_a = User.objects.create_user(
            username="ops-manager-a", email="ops-manager-a@example.invalid", password="test-only",
            role=cls.manager_role, branch=cls.branch_a,
        )
        cls.manager_b = User.objects.create_user(
            username="ops-manager-b", email="ops-manager-b@example.invalid", password="test-only",
            role=cls.manager_role, branch=cls.branch_b,
        )
        cls.customer_a = User.objects.create_user(
            username="ops-customer-a", email="ops-customer-a@example.invalid", password="test-only",
            role=cls.customer_role, branch=cls.branch_a,
        )
        cls.customer_b = User.objects.create_user(
            username="ops-customer-b", email="ops-customer-b@example.invalid", password="test-only",
            role=cls.customer_role, branch=cls.branch_b,
        )
        cls.account_a = Account.objects.create(
            user=cls.customer_a, account_number="OPS-A001",
            account_type="Savings", balance=Decimal("20000"),
            created_at=timezone.now(),
        )
        cls.account_b = Account.objects.create(
            user=cls.customer_b, account_number="OPS-B001",
            account_type="Savings", balance=Decimal("30000"),
            created_at=timezone.now(),
        )
        cls.tx_a = Transaction.objects.create(
            account=cls.account_a, amount=Decimal("1000"),
            transaction_type="Withdrawal", merchant="Market A",
            location="Kochi", transaction_time=timezone.now(),
            status="Completed", is_anomaly=1,
        )
        cls.tx_b = Transaction.objects.create(
            account=cls.account_b, amount=Decimal("1500"),
            transaction_type="Purchase", merchant="Market B",
            location="Kannur", transaction_time=timezone.now(),
            status="Completed", is_anomaly=1,
        )
        cls.alert_a = Alert.objects.create(
            alert_type="Fraud / Anomaly", severity="High",
            message="Synthetic alert A", is_resolved=False,
            created_at=timezone.now(), transaction=cls.tx_a,
        )
        cls.alert_b = Alert.objects.create(
            alert_type="Fraud / Anomaly", severity="High",
            message="Synthetic alert B", is_resolved=False,
            created_at=timezone.now(), transaction=cls.tx_b,
        )

    def setUp(self):
        self.client = APIClient()

    def as_user(self, user):
        self.client.force_authenticate(user=user)

    def test_manager_operations_are_branch_scoped_and_bounded(self):
        self.as_user(self.manager_a)
        resp = self.client.get("/api/operations/")
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data["scope"]["role"], "Manager")
        self.assertEqual({a["account_id"] for a in resp.data["accounts"]}, {self.account_a.pk})
        self.assertEqual({t["transaction_id"] for t in resp.data["transactions"]}, {self.tx_a.pk})
        self.assertEqual({a["alert_id"] for a in resp.data["alerts"]}, {self.alert_a.pk})
        self.assertEqual(
            self.client.get(f"/api/operations/?account_id={self.account_b.pk}").status_code,
            403,
        )
        self.assertEqual(
            self.client.get("/api/operations/?account_id=not-an-integer").status_code,
            400,
        )

    def test_branch_manager_cannot_read_admin_actions_from_other_branches(self):
        # Admin's home branch is A, but this action refers to account B.
        # Legacy user-branch filtering alone would have leaked the audit text.
        AuditLog.objects.create(
            user=self.admin,
            action=f"Sensitive cross-branch action on account {self.account_b.pk}",
            ip_address="127.0.0.1",
            log_time=timezone.now(),
        )
        self.as_user(self.manager_a)
        ops = self.client.get("/api/operations/")
        self.assertEqual(ops.status_code, 200)
        self.assertNotIn(
            "Sensitive cross-branch action",
            str(ops.data.get("audit_logs")),
        )
        logs = self.client.get("/api/audit-logs/")
        self.assertEqual(logs.status_code, 200)
        self.assertNotIn("Sensitive cross-branch action", str(logs.data))

    def test_customer_cannot_open_operational_dashboard(self):
        self.as_user(self.customer_a)
        self.assertEqual(self.client.get("/api/operations/").status_code, 403)

    def test_resolve_alert_requires_reason_preserves_fields_and_audits(self):
        self.as_user(self.manager_a)
        url = f"/api/alerts/{self.alert_a.pk}/"
        original = self.alert_a.message
        bad = self.client.patch(
            url, {"is_resolved": True, "resolution_note": "short"}, format="json",
        )
        self.assertEqual(bad.status_code, 400)
        tamper = self.client.patch(
            url, {"is_resolved": True, "resolution_note": "Reviewed as a false alert.",
                  "message": "Altered evidence"}, format="json",
        )
        self.assertEqual(tamper.status_code, 400)
        denied = self.client.patch(
            f"/api/alerts/{self.alert_b.pk}/",
            {"is_resolved": True, "resolution_note": "Outside branch alert"},
            format="json",
        )
        self.assertEqual(denied.status_code, 404)

        accepted = self.client.patch(
            url, {"is_resolved": True, "resolution_note": "Reviewed and resolved: synthetic case."},
            format="json",
        )
        self.assertEqual(accepted.status_code, 200, accepted.data)
        self.alert_a.refresh_from_db()
        self.assertTrue(self.alert_a.is_resolved)
        self.assertEqual(self.alert_a.message, original)
        self.assertEqual(self.alert_a.severity, "High")
        self.assertEqual(
            AuditLog.objects.filter(
                user=self.manager_a,
                action__contains="Reviewed and resolved: synthetic case.",
            ).count(), 1,
        )
        again = self.client.patch(
            url, {"is_resolved": True, "resolution_note": "Attempt duplicate review."},
            format="json",
        )
        self.assertEqual(again.status_code, 400)
        self.assertEqual(AuditLog.objects.filter(user=self.manager_a).count(), 1)
        visible = self.client.get("/api/operations/")
        self.assertTrue(next(
            a["is_resolved"] for a in visible.data["alerts"]
            if a["alert_id"] == self.alert_a.pk
        ))

    def test_admin_cannot_fabricate_alerts_or_delete_evidence(self):
        self.as_user(self.admin)
        url = f"/api/alerts/{self.alert_a.pk}/"
        self.assertEqual(self.client.delete(url).status_code, 405)
        self.assertEqual(self.client.put(url, {"message": "fake"}, format="json").status_code, 405)
        self.assertEqual(self.client.post("/api/alerts/", {}, format="json").status_code, 405)


@override_settings(RESEARCH_EVAL_CACHE_SECONDS=900)
class CachedEvaluationsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        role = Role.objects.create(role_name="Customer")
        branch = Branch.objects.create(
            branch_name="Cache Branch", city="Kochi", state="Kerala",
            ifsc_code="CACHE000001", phone="9000000003",
        )
        user = User.objects.create_user(
            username="cache-user", email="cache-user@example.invalid", password="test-only", role=role, branch=branch,
        )
        cls.account = Account.objects.create(
            user=user, account_number="CACHE001", account_type="Savings",
            balance=Decimal("10000.00"), created_at=timezone.now(),
        )

    def setUp(self):
        cache.clear()

    def add_transaction(self, amount, when=None):
        from datetime import datetime, timezone as dt_timezone
        return Transaction.objects.create(
            account=self.account, amount=Decimal(amount),
            transaction_type="Purchase", merchant="Market",
            location="Kochi",
            transaction_time=when or datetime(2025, 6, 15, tzinfo=dt_timezone.utc),
            status="Completed", is_anomaly=0,
        )

    def test_reuses_expensive_fits_and_invalidates_on_append(self):
        with patch(
            "finance.services.cached_research.evaluate_fraud_models",
            return_value={"dataset": 1},
        ) as fraud, patch(
            "finance.services.cached_research.evaluate_forecast_models",
            return_value={"number_of_months": 24},
        ) as forecast:
            first = get_cached_research_evaluations()
            second = get_cached_research_evaluations()
            self.assertFalse(first["cache"]["hit"])
            self.assertTrue(second["cache"]["hit"])
            self.assertEqual(fraud.call_count, 1)
            self.assertEqual(forecast.call_count, 1)
            key_before = research_dataset_fingerprint()
            self.add_transaction("115.50")
            self.assertNotEqual(research_dataset_fingerprint(), key_before)
            third = get_cached_research_evaluations()
            self.assertFalse(third["cache"]["hit"])
            self.assertEqual(fraud.call_count, 2)
            self.assertEqual(forecast.call_count, 2)

    def test_presenter_transaction_does_not_invalidate_frozen_research(self):
        from datetime import datetime, timezone as dt_timezone
        self.add_transaction("400.00")
        original = research_dataset_fingerprint()
        self.add_transaction(
            "999999.00",
            when=datetime(2026, 10, 17, tzinfo=dt_timezone.utc),
        )
        self.assertEqual(
            research_dataset_fingerprint(), original,
            "Live demo activity must not change the fixed research cohort.",
        )

    def test_forecasting_stays_at_twenty_four_months_after_demo_post(self):
        from datetime import datetime, timezone as dt_timezone
        from finance.services.forecast_service import get_monthly_transaction_data
        Transaction.objects.all().delete()
        for year, month in [(2024, 1), (2025, 12)]:
            Transaction.objects.create(
                account=self.account, amount=Decimal("300.00"),
                transaction_type="Deposit", merchant="Source", location="Kochi",
                transaction_time=datetime(year, month, 15, tzinfo=dt_timezone.utc),
                status="Completed", is_anomaly=0,
            )
            Transaction.objects.create(
                account=self.account, amount=Decimal("100.00"),
                transaction_type="Purchase", merchant="Vendor", location="Kochi",
                transaction_time=datetime(year, month, 15, tzinfo=dt_timezone.utc),
                status="Completed", is_anomaly=0,
            )
        self.add_transaction(
            "999999.00",
            when=datetime(2026, 10, 17, tzinfo=dt_timezone.utc),
        )
        data = get_monthly_transaction_data()
        self.assertEqual(len(data["income"]), 24)
        self.assertEqual(len(data["expense"]), 24)
        self.assertEqual(data["income"].index.max().strftime("%Y-%m"), "2025-12")

    def test_stale_cache_is_not_used_after_amount_sum_changes(self):
        self.add_transaction("400.00")
        before = research_dataset_fingerprint()
        Transaction.objects.update(amount=Decimal("405.00"))
        self.assertNotEqual(before, research_dataset_fingerprint())


class GeminiIntegrityTests(TestCase):
    def fixture(self):
        return {
            "fraud_evaluation": {
                "dataset": 50000, "actual_anomalies": 500,
                "statistical_baseline": {"f1": 0.7},
                "isolation_forest": {"f1": 0.044},
            },
            "forecast_evaluation": {
                "income": {
                    "models": {
                        "seasonal_naive": {"mape": 7.83},
                        "sarima": {"mape": 61.62},
                    },
                    "validation": {"observations": 11, "sarima_observations": 10},
                },
            },
        }

    def test_report_numbers_are_python_computed(self):
        verified = self.fixture()
        section = render_verified_numeric_report(verified)
        self.assertIn("50000", section)
        self.assertIn("70.00%", section)
        self.assertIn("4.40%", section)
        self.assertIn("7.83%", section)
        self.assertIn("10", section)

    def test_fabricated_numbers_or_guarantees_are_rejected(self):
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValueError):
            validate_narrative("Fraud reduced by 99 percent.")
        with self.assertRaises(ValueError):
            validate_narrative("The forecast is guaranteed.")
        self.assertIn("synthetic", validate_narrative("This synthetic dataset has major limitations."))

    def test_valid_mocked_gemini_narrative_does_not_control_metrics(self):
        evidence = self.fixture()
        mock_client = SimpleNamespace(models=SimpleNamespace(
            generate_content=lambda **kwargs: SimpleNamespace(
                text="## Observations\nThe statistical baseline is stronger here.\n## Limitations\nSynthetic events are not fraud evidence."
            )
        ))
        with patch("finance.services.gemini_service.get_verified_results",
                   return_value=evidence), patch(
            "finance.services.gemini_service.get_gemini_client",
            return_value=mock_client,
        ):
            report = generate_gemini_report()
        self.assertEqual(report["report_source"], "gemini")
        self.assertIn("50000", report["report"])
        self.assertEqual(report["numeric_claims_source"], "python_only")

    def test_rejected_mocked_gemini_response_falls_back_safely(self):
        evidence = self.fixture()
        mock_client = SimpleNamespace(models=SimpleNamespace(
            generate_content=lambda **kwargs: SimpleNamespace(
                text="We have detected 90000 bank frauds!"
            )
        ))
        with patch("finance.services.gemini_service.get_verified_results",
                   return_value=evidence), patch(
            "finance.services.gemini_service.get_gemini_client",
            return_value=mock_client,
        ):
            report = generate_gemini_report()
        self.assertEqual(report["report_source"], "fallback")
        self.assertIn("50000", report["report"])
        self.assertNotIn("90000", report["report"])
