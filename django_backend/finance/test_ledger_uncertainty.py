"""Tests for an ISOLATED synthetic ledger and cautiously empirical intervals."""
from decimal import Decimal

import numpy as np
import pandas as pd
from django.test import TestCase, SimpleTestCase
from django.utils import timezone
from rest_framework.test import APIClient

from finance.models import (
    Account, AuditLog, Branch, Role, SyntheticLedgerAccount,
    SyntheticLedgerLine, SyntheticLedgerPosting, User,
)
from finance.services.synthetic_ledger import reconcile_synthetic_ledger
from finance.services.forecast_uncertainty import horizon_uncertainty


class BalancedSyntheticLedgerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.role_admin = Role.objects.create(role_name="Admin")
        cls.role_manager = Role.objects.create(role_name="Manager")
        cls.role_customer = Role.objects.create(role_name="Customer")
        cls.branch = Branch.objects.create(
            branch_name="Demo Kochi", city="Kochi", state="Kerala",
            ifsc_code="TESTLEDGER01", phone="9000001234",
        )
        cls.other_branch = Branch.objects.create(
            branch_name="Demo Kannur", city="Kannur", state="Kerala",
            ifsc_code="TESTLEDGER02", phone="9000001235",
        )
        cls.admin = User.objects.create_user(
            username="ledger_admin", email="ledger_admin@example.invalid",
            password="test-only", role=cls.role_admin, branch=cls.branch,
        )
        cls.manager = User.objects.create_user(
            username="ledger_manager", email="ledger_manager@example.invalid",
            password="test-only", role=cls.role_manager, branch=cls.branch,
        )
        cls.own_customer = User.objects.create_user(
            username="ledger_customer", email="ledger_customer@example.invalid",
            password="test-only", role=cls.role_customer, branch=cls.branch,
        )
        cls.other_customer = User.objects.create_user(
            username="ledger_other", email="ledger_other@example.invalid",
            password="test-only", role=cls.role_customer, branch=cls.other_branch,
        )
        cls.first = Account.objects.create(
            user=cls.own_customer, account_number="SIMLEDGER001",
            account_type="Savings", balance=Decimal("888.00"),
            created_at=timezone.now(),
        )
        cls.second = Account.objects.create(
            user=cls.own_customer, account_number="SIMLEDGER002",
            account_type="Savings", balance=Decimal("777.00"),
            created_at=timezone.now(),
        )
        cls.external = Account.objects.create(
            user=cls.other_customer, account_number="SIMLEDGER003",
            account_type="Savings", balance=Decimal("666.00"),
            created_at=timezone.now(),
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def post(self, operation, key, amount="100.00", account=None, destination=None, **extra):
        return self.client.post("/api/synthetic-ledger/", {
            "operation": operation, "idempotency_key": key,
            "amount": amount, "account_id": (account or self.first).pk,
            **({"destination_account_id": destination.pk} if destination else {}),
            **extra,
        }, format="json")

    def test_balanced_deposit_duplicate_protection_and_reconciliation(self):
        resp = self.post("deposit", "initial-funding-0001")
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertTrue(resp.data["posting"]["balanced"])
        self.assertEqual(len(resp.data["posting"]["lines"]), 2)
        self.assertEqual(SyntheticLedgerPosting.objects.count(), 1)
        self.assertEqual(str(SyntheticLedgerAccount.objects.get(account=self.first).balance), "100.00")
        # Original benchmark/demo Account.balance must be left unchanged.
        self.first.refresh_from_db()
        self.assertEqual(self.first.balance, Decimal("888.00"))
        again = self.post("deposit", "initial-funding-0001")
        self.assertEqual(again.status_code, 200, again.data)
        self.assertFalse(again.data["created"])
        self.assertEqual(SyntheticLedgerPosting.objects.count(), 1)
        collision = self.post("deposit", "initial-funding-0001", amount="200.00")
        self.assertEqual(collision.status_code, 400)
        self.assertTrue(reconcile_synthetic_ledger()["balanced"])
        self.assertEqual(AuditLog.objects.filter(user=self.admin).count(), 1)

    def test_atomic_overdraft_and_malformed_amount_rejected_without_artifacts(self):
        too_much = self.post("withdrawal", "reject-overdraft-0001", "5.00")
        self.assertEqual(too_much.status_code, 400)
        for bad in ("-1.00", "0", "1.123", "NaN"):
            result = self.post("deposit", "bad-money-"+bad.replace(".", ""), bad)
            self.assertEqual(result.status_code, 400)
        self.assertEqual(SyntheticLedgerPosting.objects.count(), 0)
        self.assertEqual(SyntheticLedgerLine.objects.count(), 0)
        self.assertEqual(AuditLog.objects.count(), 0)

    def test_transfer_one_time_reversal_and_retry(self):
        self.assertEqual(self.post("deposit", "fund-before-transfer-0001").status_code, 201)
        transfer = self.post("transfer", "move-to-other-wallet-0001",
                             amount="40.00", destination=self.second)
        self.assertEqual(transfer.status_code, 201, transfer.data)
        self.assertEqual(str(SyntheticLedgerAccount.objects.get(account=self.first).balance), "60.00")
        self.assertEqual(str(SyntheticLedgerAccount.objects.get(account=self.second).balance), "40.00")
        reversal = self.post(
            "reversal", "undo-transfer-once-0001", amount="40.00",
            reversal_posting_id=transfer.data["posting"]["posting_id"],
        )
        self.assertEqual(reversal.status_code, 201, reversal.data)
        retry = self.post(
            "reversal", "undo-transfer-once-0001", amount="40.00",
            reversal_posting_id=transfer.data["posting"]["posting_id"],
        )
        self.assertEqual(retry.status_code, 200, retry.data)
        self.assertEqual(self.post(
            "reversal", "different-reversal-key-0001", amount="40.00",
            reversal_posting_id=transfer.data["posting"]["posting_id"],
        ).status_code, 400)
        self.assertEqual(str(SyntheticLedgerAccount.objects.get(account=self.first).balance), "100.00")
        self.assertEqual(str(SyntheticLedgerAccount.objects.get(account=self.second).balance), "0.00")
        self.assertTrue(reconcile_synthetic_ledger()["balanced"])
        self.assertEqual(SyntheticLedgerPosting.objects.count(), 3)

    def test_manager_cannot_access_foreign_branch_or_see_its_postings(self):
        self.assertEqual(
            self.post("deposit", "other-branch-owned-0001", account=self.external).status_code, 201
        )
        self.client.force_authenticate(user=self.manager)
        forbidden = self.post("deposit", "manager-forbidden-0001", account=self.external)
        self.assertEqual(forbidden.status_code, 403)
        forbidden_transfer = self.post("transfer", "manager-cross-branch-0001",
                                        destination=self.external)
        self.assertEqual(forbidden_transfer.status_code, 403)
        result = self.client.get("/api/synthetic-ledger/")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data["scope"], "Manager")
        self.assertFalse(result.data["postings"])
        self.assertIsNone(result.data["reconciliation"])
        self.client.force_authenticate(user=self.own_customer)
        self.assertEqual(self.client.get("/api/synthetic-ledger/").status_code, 403)
        self.assertEqual(self.post("deposit", "forbidden-customer-0001").status_code, 403)

    def test_imbalance_is_detected_not_hidden(self):
        self.assertEqual(self.post("deposit", "reconcile-pair-0001").status_code, 201)
        wallet = SyntheticLedgerAccount.objects.get(account=self.first)
        wallet.balance = Decimal("999.99")
        wallet.save(update_fields=["balance"])
        audit = reconcile_synthetic_ledger()
        self.assertFalse(audit["balanced"])
        self.assertTrue(any("mismatched_balance" in issue for issue in audit["issues"]))


class EmpiricalIntervalTests(SimpleTestCase):
    def setUp(self):
        self.series = pd.Series(
            [float(100 + (i % 12) * 7 + (i//12)*3) for i in range(24)],
            index=pd.date_range("2024-01-01", periods=24, freq="MS"),
        )

    def test_horizon_calibration_only_where_enough_residuals(self):
        data = horizon_uncertainty(self.series, maximum_horizon=12)
        self.assertEqual(len(data), 12)
        self.assertEqual(data[0]["calibration_samples"], 11)
        self.assertEqual(data[3]["calibration_samples"], 8)
        self.assertEqual(data[0]["status"], "illustrative_empirical_interval")
        self.assertEqual(data[3]["status"], "illustrative_empirical_interval")
        self.assertIsNotNone(data[0]["lower"])
        self.assertLessEqual(data[0]["lower"], data[0]["point_forecast"])
        self.assertGreaterEqual(data[0]["upper"], data[0]["point_forecast"])
        for row in data[4:]:
            self.assertEqual(row["status"], "insufficient_calibration")
            self.assertIsNone(row["lower"])
            self.assertIsNone(row["upper"])

    def test_no_fake_intervals_for_short_histories_or_bad_confidence(self):
        tiny = self.series.iloc[:13]
        result = horizon_uncertainty(tiny, 12)
        self.assertTrue(all(x["lower"] is None for x in result))
        with self.assertRaises(ValueError):
            horizon_uncertainty(self.series, 12, confidence=0.99)
        with self.assertRaises(ValueError):
            horizon_uncertainty(self.series, 25)
