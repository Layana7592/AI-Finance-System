"""Isolated, strictly balanced synthetic double-entry simulator.

This MUST NOT modify original Transaction, JournalEntry, or Account.balance
records, which are preserved as a different academic analytics experiment.
Asset-style demo wallets: DR increases wallet balance; CR decreases it.
The system clearing account has the inverse signed position.
"""
import hashlib
import json
from decimal import Decimal, InvalidOperation

from django.db import transaction as db_transaction
from django.db.models import Sum
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound

from finance.models import (
    Account, SyntheticLedgerAccount, SyntheticLedgerPosting, SyntheticLedgerLine,
)

CENT = Decimal("0.01")
MAX = Decimal("9999999999999.99")


def _money(value):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValidationError("Invalid monetary amount.") from exc
    if not amount.is_finite() or amount <= 0 or amount > MAX or amount != amount.quantize(CENT):
        raise ValidationError("Amount must be positive, finite and have at most 2 decimals.")
    return amount


def assert_can_post(user, account):
    if not user or not user.is_authenticated or not user.role:
        raise PermissionDenied("A signed-in reviewer is required.")
    if user.role.role_name == "Admin":
        return
    if user.role.role_name == "Manager" and account.user.branch_id == user.branch_id:
        return
    raise PermissionDenied("Synthetic wallet is outside the authorized branch.")


def _wallet(account):
    if account is None:
        wallet, _ = SyntheticLedgerAccount.objects.get_or_create(
            code="SYSTEM-CLEARING",
            defaults={"is_system_clearing": True},
        )
    else:
        wallet, _ = SyntheticLedgerAccount.objects.get_or_create(
            account=account,
            defaults={"code": f"WALLET-{account.pk}", "is_system_clearing": False},
        )
    return wallet


def _post_lines(posting, debited_wallet, credited_wallet, amount):
    if debited_wallet.pk == credited_wallet.pk:
        raise ValidationError("Debit and credit wallets cannot be identical.")
    # Lock in stable order; reject overdrafts atomically.
    locked = {
        w.pk: w for w in SyntheticLedgerAccount.objects.select_for_update().filter(
            pk__in=[debited_wallet.pk, credited_wallet.pk]
        ).order_by("pk")
    }
    d, c = locked[debited_wallet.pk], locked[credited_wallet.pk]
    if not c.is_system_clearing and c.balance < amount:
        raise ValidationError("Insufficient synthetic wallet funds.")
    d.balance += amount
    c.balance -= amount
    d.save(update_fields=["balance"])
    c.save(update_fields=["balance"])
    SyntheticLedgerLine.objects.bulk_create([
        SyntheticLedgerLine(posting=posting, ledger_account=d, side="DR", amount=amount),
        SyntheticLedgerLine(posting=posting, ledger_account=c, side="CR", amount=amount),
    ])


def _fingerprint(operation, amount, source_id, target_id, original_id, actor_id, memo):
    obj = {
        "operation": operation, "amount": str(amount), "source": source_id,
        "target": target_id, "reversal": original_id, "actor": actor_id,
        "memo": memo,
    }
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode("utf-8")).hexdigest()


@db_transaction.atomic
def post_ledger_operation(*, user, operation, amount=None, account_id=None,
                          destination_account_id=None, idempotency_key, memo="",
                          reversal_posting_id=None):
    if not isinstance(idempotency_key, str) or not 8 <= len(idempotency_key) <= 120:
        raise ValidationError("A unique idempotency key (8–120 characters) is required.")
    if not isinstance(memo, str) or len(memo) > 500:
        raise ValidationError("Memo must have at most 500 characters.")
    if operation not in {"deposit", "withdrawal", "transfer", "reversal"}:
        raise ValidationError("Unsupported simulated ledger operation.")
    if not user or not user.is_authenticated or not user.role or user.role.role_name not in ("Admin", "Manager"):
        raise PermissionDenied("Only Admin and authorized Manager may post to demo ledger.")

    original = None
    if operation == "reversal":
        if not reversal_posting_id:
            raise ValidationError("Reversal requires an original posting ID.")
        try:
            original = SyntheticLedgerPosting.objects.select_for_update().get(pk=reversal_posting_id)
        except SyntheticLedgerPosting.DoesNotExist as exc:
            raise NotFound("Original posting does not exist.") from exc
        if original.operation == "reversal":
            raise ValidationError("Cannot reverse a reversal.")
        source = original.source_account
        target = original.destination_account
        if source:
            assert_can_post(user, source)
        if target:
            assert_can_post(user, target)
        value = original.amount
    else:
        value = _money(amount)
        try:
            source = Account.objects.select_related("user", "user__role").get(pk=account_id) if account_id else None
            target = Account.objects.select_related("user", "user__role").get(pk=destination_account_id) if destination_account_id else None
        except (Account.DoesNotExist, ValueError, TypeError) as exc:
            raise NotFound("Synthetic ledger account not found.") from exc
        if operation in ("withdrawal", "deposit") and (source is None or target is not None):
            raise ValidationError("Deposit/withdrawal requires one account and no destination.")
        if operation == "transfer" and (source is None or target is None or source.pk == target.pk):
            raise ValidationError("Transfers require distinct source and destination accounts.")
        assert_can_post(user, source)
        if target:
            assert_can_post(user, target)

    source_id = source.pk if source else None
    target_id = target.pk if target else None
    request_hash = _fingerprint(operation, value, source_id, target_id,
                                original.pk if original else None, user.pk, memo)
    prior = SyntheticLedgerPosting.objects.filter(idempotency_key=idempotency_key).first()
    if prior:
        if prior.request_fingerprint != request_hash:
            raise ValidationError("Idempotency key was previously used for a different request.")
        return prior, False
    if original and SyntheticLedgerPosting.objects.filter(reversal_of=original).exists():
        raise ValidationError("This posting has already been reversed.")

    posting, created = SyntheticLedgerPosting.objects.get_or_create(
        idempotency_key=idempotency_key,
        defaults={
            "actor": user, "operation": operation, "amount": value,
            "source_account": source, "destination_account": target,
            "memo": memo, "request_fingerprint": request_hash,
            "reversal_of": original,
        },
    )
    if not created:
        if posting.request_fingerprint != request_hash:
            raise ValidationError("Idempotency key conflict.")
        return posting, False

    src_wallet = _wallet(source) if source else None
    dst_wallet = _wallet(target) if target else None
    clearing = _wallet(None) if operation in ("deposit", "withdrawal") else None
    if operation == "deposit":
        _post_lines(posting, src_wallet, clearing, value)
    elif operation == "withdrawal":
        _post_lines(posting, clearing, src_wallet, value)
    elif operation == "transfer":
        _post_lines(posting, dst_wallet, src_wallet, value)
    else:
        # Restore EXACTLY the original two legs, reversed. A spent recipient
        # balance means the attempted reversal is rejected, not overdrafted.
        original_lines = list(original.lines.select_related("ledger_account"))
        if len(original_lines) != 2:
            raise ValidationError("Original posting lacks exactly two ledger lines.")
        debits = [line for line in original_lines if line.side == "DR"]
        credits = [line for line in original_lines if line.side == "CR"]
        if len(debits) != 1 or len(credits) != 1:
            raise ValidationError("Original posting has invalid debit/credit structure.")
        _post_lines(posting, credits[0].ledger_account, debits[0].ledger_account, value)
    return posting, True


def reconcile_synthetic_ledger():
    """Verify every balanced posting and the actual wallet totals against lines."""
    issues = []
    for post in SyntheticLedgerPosting.objects.prefetch_related("lines").all():
        lines = list(post.lines.all())
        debits = sum((x.amount for x in lines if x.side == "DR"), Decimal("0"))
        credits = sum((x.amount for x in lines if x.side == "CR"), Decimal("0"))
        if len(lines) != 2 or debits != credits or debits != post.amount:
            issues.append(f"posting:{post.pk}:unbalanced")
    total = Decimal("0")
    wallets = SyntheticLedgerAccount.objects.all()
    for wallet in wallets:
        dr = wallet.posted_lines.filter(side="DR").aggregate(s=Sum("amount"))["s"] or Decimal("0")
        cr = wallet.posted_lines.filter(side="CR").aggregate(s=Sum("amount"))["s"] or Decimal("0")
        expected = dr - cr
        if expected != wallet.balance:
            issues.append(f"wallet:{wallet.pk}:mismatched_balance")
        if not wallet.is_system_clearing and wallet.balance < 0:
            issues.append(f"wallet:{wallet.pk}:negative")
        total += wallet.balance
    if total != 0:
        issues.append("all_wallet_balances_do_not_sum_to_zero")
    return {
        "balanced": not issues,
        "issues": issues,
        "postings": SyntheticLedgerPosting.objects.count(),
        "wallets": wallets.count(),
        "total_balance": str(total),
        "legacy_analytics_account_balance_reconciliation": "not_applicable_isolated_simulator",
    }
