"""Regression tests for the bounded live fraud path and safe forecasting.

Run:
    python manage.py test finance.test_workflow_stability
"""
from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
from unittest.mock import patch

import numpy as np
import pandas as pd
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .models import (
    Role, Branch, User, Account, Transaction,
    FraudPrediction, FinancialForecast, Alert, AuditLog,
)
from .services.forecast_service import (
    calculate_metrics, expanding_window_validation, generate_forecast,
    get_monthly_transaction_data,
)


class LiveTransactionScreenTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        role, _ = Role.objects.get_or_create(role_name="Admin")
        branch = Branch.objects.create(
            branch_name="Workflow branch", city="Kochi",
            state="Kerala", ifsc_code="WORK000001", phone="9000000004",
        )
        cls.user = User.objects.create_user(
            username="workflowadmin", email="workflowadmin@example.org",
            password="StrongPassword123!", role=role, branch=branch,
        )
        cls.account = Account.objects.create(
            user=cls.user, account_number="WORKFLOW-001",
            account_type="Savings", balance=Decimal("10000.00"),
            created_at=timezone.now(),
        )

    def transaction_payload(self, amount="1000.00"):
        return {
            "account": self.account.account_id,
            "amount": amount,
            "transaction_type": "Withdrawal",
            "merchant": "Unknown new merchant",
            "location": "Unknown new location",
            "transaction_time": datetime(2025, 6, 21, 23, 0, tzinfo=dt_timezone.utc).isoformat(),
            "status": "Completed",
        }

    def client_for_admin(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        return client

    def test_live_create_does_not_refit_isolation_forest_or_scan_every_account(self):
        client = self.client_for_admin()
        with patch(
            "finance.services.fraud_service._isolation_forest_scores",
            side_effect=AssertionError("Batch Isolation Forest must not run on POST"),
        ), patch(
            "finance.services.live_fraud_service._calculate_behavioural_risk_scores",
            return_value=[0.1],
        ) as scorer:
            response = client.post("/api/transactions/", self.transaction_payload(), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(scorer.call_count, 1)
        self.assertEqual(FraudPrediction.objects.count(), 1)
        self.assertEqual(Alert.objects.count(), 0)
        prediction = FraudPrediction.objects.get()
        self.assertEqual(prediction.model_version, "BehaviouralRiskHeuristic-v1")
        self.assertFalse(prediction.prediction)
        self.assertIn("created and screened", AuditLog.objects.get().action)

    def test_high_risk_transaction_creates_one_alert(self):
        base = datetime(2025, 6, 1, 10, 0, tzinfo=dt_timezone.utc)
        for index, amount in enumerate((85, 90, 95, 100, 105, 110, 115)):
            Transaction.objects.create(
                account=self.account, amount=Decimal(amount),
                transaction_type="Deposit", merchant="Known merchant",
                location="Known location", transaction_time=base + timedelta(days=index),
                status="Completed", is_anomaly=0,
            )
        response = self.client_for_admin().post(
            "/api/transactions/", self.transaction_payload(amount="100000.00"), format="json"
        )
        self.assertEqual(response.status_code, 201, response.data)
        prediction = FraudPrediction.objects.get()
        self.assertTrue(prediction.prediction)
        self.assertEqual(Alert.objects.filter(transaction=prediction.transaction).count(), 1)
        self.assertGreaterEqual(float(prediction.fraud_probability), 0.60)

    def test_live_screen_has_a_bounded_account_only_history(self):
        base = datetime(2025, 1, 1, 10, 0, tzinfo=dt_timezone.utc)
        for index in range(300):
            Transaction.objects.create(
                account=self.account, amount=Decimal("100.00"),
                transaction_type="Deposit", merchant="Known",
                location="Kochi",
                transaction_time=base + timedelta(hours=index),
                status="Completed", is_anomaly=0,
            )

        def check_history(items):
            self.assertLessEqual(len(items), 251)
            self.assertTrue(all(tx.account_id == self.account.pk for tx in items))
            return [0.0] * len(items)

        with patch(
            "finance.services.live_fraud_service._calculate_behavioural_risk_scores",
            side_effect=check_history,
        ) as scorer:
            response = self.client_for_admin().post(
                "/api/transactions/", self.transaction_payload(), format="json"
            )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(scorer.call_count, 1)

    def test_failure_rolls_back_transaction_prediction_and_alert(self):
        with patch("finance.views.create_audit_log", side_effect=RuntimeError("audit unavailable")):
            with self.assertRaises(RuntimeError):
                self.client_for_admin().post(
                    "/api/transactions/", self.transaction_payload(), format="json"
                )
        self.assertEqual(Transaction.objects.count(), 0)
        self.assertEqual(FraudPrediction.objects.count(), 0)
        self.assertEqual(Alert.objects.count(), 0)

    def test_transactions_are_immutable_after_creation(self):
        existing = Transaction.objects.create(
            account=self.account, amount=Decimal("100.00"),
            transaction_type="Deposit", merchant="Existing",
            location="Kochi", transaction_time=timezone.now(),
            status="Completed", is_anomaly=0,
        )
        client = self.client_for_admin()
        self.assertEqual(
            client.patch(f"/api/transactions/{existing.pk}/", {"amount": "1.00"}).status_code,
            405,
        )
        self.assertEqual(client.delete(f"/api/transactions/{existing.pk}/").status_code, 405)


class ForecastSafetyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        role, _ = Role.objects.get_or_create(role_name="Admin")
        branch = Branch.objects.create(
            branch_name="Forecast workflow branch", city="Kochi",
            state="Kerala", ifsc_code="WORK000002", phone="9000000005",
        )
        cls.user = User.objects.create_user(
            username="forecastworkflowadmin", email="fworkflow@example.org",
            password="StrongPassword123!", role=role, branch=branch,
        )
        cls.account = Account.objects.create(
            user=cls.user, account_number="WORKFLOW-002",
            account_type="Savings", balance=Decimal("10000.00"),
            created_at=timezone.now(),
        )

    def admin_client(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        return client

    def test_empty_metrics_are_unknown_not_zero(self):
        self.assertEqual(
            calculate_metrics([], []), {"mae": None, "rmse": None, "mape": None}
        )

    def test_sarima_failure_does_not_discard_naive_observations(self):
        series = pd.Series(
            np.arange(1, 25, dtype=float),
            index=pd.date_range("2024-01-01", periods=24, freq="MS"),
        )
        with patch(
            "finance.services.forecast_service.sarima_forecast",
            side_effect=ValueError("cannot fit"),
        ):
            scores = expanding_window_validation(series, initial_train_size=13)
        self.assertEqual(scores["observations"], 11)
        self.assertEqual(scores["sarima_observations"], 0)
        self.assertIsNotNone(scores["seasonal_naive"]["mae"])
        self.assertIsNone(scores["sarima"]["mape"])

    def test_sarima_failure_falls_back_to_naive_forecast(self):
        index = pd.date_range("2024-01-01", periods=24, freq="MS")
        series = pd.Series(np.arange(1, 25, dtype=float), index=index)
        evaluation = {
            "seasonal_naive": {"mape": 10.0},
            "sarima": {"mape": 5.0},
            "observations": 11,
            "sarima_observations": 11,
        }
        with patch(
            "finance.services.forecast_service.get_monthly_transaction_data",
            return_value={"income": series, "expense": series},
        ), patch(
            "finance.services.forecast_service.expanding_window_validation",
            return_value=evaluation,
        ), patch(
            "finance.services.forecast_service.sarima_forecast",
            side_effect=RuntimeError("model diverged"),
        ):
            forecast = generate_forecast(12)
        self.assertEqual(len(forecast), 12)
        self.assertEqual(forecast[0]["forecast_month"].isoformat(), "2026-01-01")
        self.assertTrue(all(item["predicted_expense"] >= 0 for item in forecast))

    def test_income_and_expense_use_same_month_index(self):
        Transaction.objects.create(
            account=self.account, amount=Decimal("1000.00"),
            transaction_type="Deposit", merchant="Test",
            location="Kochi", transaction_time=datetime(
                2024, 1, 15, tzinfo=dt_timezone.utc,
            ), status="Completed", is_anomaly=0,
        )
        Transaction.objects.create(
            account=self.account, amount=Decimal("500.00"),
            transaction_type="Payment", merchant="Test",
            location="Kochi", transaction_time=datetime(
                2024, 3, 15, tzinfo=dt_timezone.utc,
            ), status="Completed", is_anomaly=0,
        )
        data = get_monthly_transaction_data()
        self.assertEqual(len(data["income"]), 3)
        self.assertTrue(data["income"].index.equals(data["expense"].index))
        self.assertEqual(float(data["expense"].iloc[0]), 0.0)
        self.assertEqual(float(data["income"].iloc[-1]), 0.0)

    def test_invalid_forecast_horizon_does_not_change_saved_rows(self):
        original = FinancialForecast.objects.create(
            forecast_month=datetime(2026, 1, 1).date(),
            predicted_income=Decimal("100.00"),
            predicted_expense=Decimal("50.00"), generated_at=timezone.now(),
        )
        response = self.admin_client().post(
            "/api/forecasts/generate/", {"horizon": 999}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertTrue(FinancialForecast.objects.filter(pk=original.pk).exists())

    def test_failed_bulk_insert_rolls_back_deleted_forecasts(self):
        original = FinancialForecast.objects.create(
            forecast_month=datetime(2026, 1, 1).date(),
            predicted_income=Decimal("100.00"),
            predicted_expense=Decimal("50.00"), generated_at=timezone.now(),
        )
        generated = [{
            "forecast_month": datetime(2026, 2, 1).date(),
            "predicted_income": 200.0, "predicted_expense": 100.0,
        }]
        with patch("finance.services.forecast_service.generate_forecast", return_value=generated), patch.object(
            FinancialForecast.objects, "bulk_create", side_effect=RuntimeError("db insert failed"),
        ):
            response = self.admin_client().post(
                "/api/forecasts/generate/", {"horizon": 1}, format="json"
            )
        self.assertEqual(response.status_code, 500, response.data)
        self.assertEqual(FinancialForecast.objects.count(), 1)
        self.assertTrue(FinancialForecast.objects.filter(pk=original.pk).exists())
