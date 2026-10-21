"""Real token/login and full synthetic presenter workflow regression tests.

Run: python manage.py test finance.test_presenter_demo
"""
import os
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .models import (
    Account, Alert, AuditLog, Branch, FinancialForecast,
    FraudPrediction, Role, Transaction, User,
)


class PresenterDemoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Role.objects.create(role_name="Admin")
        Branch.objects.create(
            branch_name="Presenter test", city="Kannur",
            state="Kerala", ifsc_code="PRSN000001", phone="9000000300",
        )

    def setUp(self):
        with patch.dict(os.environ, {"DEMO_PRESENTER_PASSWORD": "PresenterOnly123!"}):
            call_command("prepare_demo_presenter", verbosity=0)
        self.client = APIClient()

    def login(self):
        # A fresh sign-in must NOT attach the previously revoked token.
        self.client.credentials()
        response = self.client.post(
            "/api/token/",
            {"username": "demo_presenter", "password": "PresenterOnly123!"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(response.data.get("token"))
        self.client.credentials(HTTP_AUTHORIZATION="Token " + response.data["token"])
        return response.data["token"]

    def test_presenter_is_idempotent_and_password_hashed(self):
        self.assertEqual(User.objects.filter(username="demo_presenter").count(), 1)
        user = User.objects.get(username="demo_presenter")
        self.assertNotEqual(user.password, "PresenterOnly123!")
        self.assertTrue(user.check_password("PresenterOnly123!"))
        account = Account.objects.get(account_number="DEMO-ACCOUNT-2026")
        self.assertEqual(Transaction.objects.filter(account=account).count(), 12)
        with patch.dict(os.environ, {"DEMO_PRESENTER_PASSWORD": "PresenterOnly123!"}):
            call_command("prepare_demo_presenter", verbosity=0)
        self.assertEqual(Transaction.objects.filter(account=account).count(), 12)

    def test_token_and_identity_are_protected(self):
        self.assertEqual(self.client.get("/api/me/").status_code, 401)
        self.login()
        response = self.client.get("/api/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], "demo_presenter")
        self.assertEqual(response.data["role"], "Admin")
        self.assertTrue(response.data["can_run_demo"])
        self.assertNotIn("password", response.data)
        self.assertNotIn("token", response.data)

    def test_logout_revokes_server_token_and_requires_fresh_authentication(self):
        token = self.login()
        self.assertEqual(self.client.get("/api/me/").status_code, 200)
        revoked = self.client.post("/api/logout/", {}, format="json")
        self.assertEqual(revoked.status_code, 204, revoked.data)
        self.assertEqual(self.client.get("/api/me/").status_code, 401)
        self.assertEqual(self.client.post("/api/logout/").status_code, 401)

        new_token = self.login()
        self.assertNotEqual(token, new_token)
        self.assertEqual(self.client.get("/api/me/").status_code, 200)

    def test_anonymous_cannot_revoke_a_presenter_token(self):
        self.assertEqual(self.client.post("/api/logout/").status_code, 401)

    def test_full_real_transaction_alert_audit_forecast_and_fallback_report(self):
        self.login()
        account = Account.objects.get(account_number="DEMO-ACCOUNT-2026")
        account_resp = self.client.get("/api/accounts/")
        self.assertEqual(account_resp.status_code, 200)
        self.assertTrue(any(
            record["account_id"] == account.pk
            for record in account_resp.data
        ))

        with patch("finance.views.get_dashboard_data", return_value={"summary": {"real": True}}):
            self.assertEqual(self.client.get("/api/dashboard/").status_code, 200)

        new_transaction = self.client.post("/api/transactions/", {
            "account": account.pk,
            "amount": "999999.00",
            "transaction_type": "Withdrawal",
            "merchant": "UnexpectedMerchant",
            "location": "UnusualLocation",
            "transaction_time": timezone.now().isoformat(),
            "status": "Completed",
        }, format="json")
        self.assertEqual(new_transaction.status_code, 201, new_transaction.data)
        tx_id = new_transaction.data["transaction_id"]

        prediction = FraudPrediction.objects.get(transaction_id=tx_id)
        self.assertTrue(prediction.prediction)
        self.assertGreaterEqual(float(prediction.fraud_probability), 0.60)
        self.assertEqual(prediction.model_version, "BehaviouralRiskHeuristic-v1")
        alert = Alert.objects.get(transaction_id=tx_id)
        self.assertFalse(alert.is_resolved)
        self.assertTrue(AuditLog.objects.filter(
            action__contains="Transaction " + str(tx_id) + " created"
        ).exists())

        forecast_date = timezone.now().date().replace(day=1)
        for offset in range(12):
            FinancialForecast.objects.create(
                forecast_month=forecast_date + timedelta(days=31 * offset),
                predicted_income=Decimal("10000.00"),
                predicted_expense=Decimal("8000.00"),
                generated_at=timezone.now(),
            )
        forecast_resp = self.client.get("/api/forecasts/")
        self.assertEqual(forecast_resp.status_code, 200)
        self.assertEqual(len(forecast_resp.data), 12)

        payload = {
            "report_source": "fallback",
            "gemini_available": False,
            "report": "# Verified management report\nGemini is unavailable.",
            "verified_results": {"fraud_evaluation": {"dataset": 13}},
        }
        with patch("finance.views.generate_gemini_report", return_value=payload):
            report = self.client.get("/api/report/")
        self.assertEqual(report.status_code, 200, report.data)
        self.assertEqual(report.data["report_source"], "fallback")
        self.assertEqual(report.data["verified_results"], payload["verified_results"])
        self.assertTrue(AuditLog.objects.filter(
            action__contains="Gemini management financial report"
        ).exists())
