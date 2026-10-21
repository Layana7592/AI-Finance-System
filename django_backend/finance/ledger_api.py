"""Authenticated, branch-scoped APIs for isolated synthetic double-entry entries."""
from decimal import Decimal

from django.db import transaction as db_transaction
from django.db.models import Q
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied

from finance.models import SyntheticLedgerAccount, SyntheticLedgerPosting
from finance.services.audit_service import create_audit_log
from finance.services.synthetic_ledger import (
    post_ledger_operation, reconcile_synthetic_ledger,
)


class PostingRequest(serializers.Serializer):
    operation = serializers.ChoiceField(choices=("deposit", "withdrawal", "transfer", "reversal"))
    idempotency_key = serializers.CharField(min_length=8, max_length=120)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    account_id = serializers.IntegerField(min_value=1, required=False)
    destination_account_id = serializers.IntegerField(min_value=1, required=False)
    reversal_posting_id = serializers.IntegerField(min_value=1, required=False)
    memo = serializers.CharField(max_length=500, allow_blank=True, required=False, default="")


def serialize_posting(post):
    lines = list(post.lines.select_related("ledger_account").order_by("pk"))
    return {
        "posting_id": post.pk, "operation": post.operation,
        "amount": str(post.amount), "idempotency_key": post.idempotency_key,
        "source_account_id": post.source_account_id,
        "destination_account_id": post.destination_account_id,
        "reversal_of_id": post.reversal_of_id,
        "posted_at": post.posted_at.isoformat(),
        "memo": post.memo,
        "balanced": len(lines) == 2 and
            sum((line.amount for line in lines if line.side == "DR"), Decimal("0")) ==
            sum((line.amount for line in lines if line.side == "CR"), Decimal("0")) == post.amount,
        "lines": [
            {"code": line.ledger_account.code, "side": line.side, "amount": str(line.amount)}
            for line in lines
        ],
    }


class SyntheticLedgerView(APIView):
    permission_classes = [IsAuthenticated]

    def _authorize(self, user):
        if not user.role or user.role.role_name not in ("Admin", "Manager"):
            raise PermissionDenied("Only Admin and Manager can access the synthetic ledger.")

    def get(self, request):
        self._authorize(request.user)
        is_admin = request.user.role.role_name == "Admin"
        wallets = SyntheticLedgerAccount.objects.filter(
            is_system_clearing=False, account__isnull=False
        ).select_related("account__user")
        postings = SyntheticLedgerPosting.objects.all()
        if not is_admin:
            branch = request.user.branch_id
            wallets = wallets.filter(account__user__branch_id=branch)
            postings = postings.filter(
                Q(source_account__isnull=True) | Q(source_account__user__branch_id=branch),
                Q(destination_account__isnull=True) | Q(destination_account__user__branch_id=branch),
            )
        return Response({
            "scope": request.user.role.role_name,
            "wallets": [
                {"account_id": w.account_id, "account_number": w.account.account_number,
                 "balance": str(w.balance), "wallet_code": w.code}
                for w in wallets.order_by("pk")[:40]
            ],
            "postings": [serialize_posting(post) for post in postings.order_by("-pk")[:25]],
            "reconciliation": reconcile_synthetic_ledger() if is_admin else None,
            "disclaimer": (
                "Separate teaching ledger. Not linked to legacy Account.balance, "
                "50k research transactions, payments or deposits."
            ),
        })

    def post(self, request):
        self._authorize(request.user)
        serializer = PostingRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data
        with db_transaction.atomic():
            posting, created = post_ledger_operation(
                user=request.user, **params
            )
            if created:
                create_audit_log(
                    request, f"SIMULATED LEDGER posting {posting.pk} {posting.operation} "
                    f"amount {posting.amount}; key recorded, never used as a payment."
                )
        posting.refresh_from_db()
        return Response(
            {"created": created, "posting": serialize_posting(posting)},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
