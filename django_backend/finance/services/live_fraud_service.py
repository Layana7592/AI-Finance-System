"""Bounded, explainable live transaction screening for the academic demo.

The benchmark Isolation Forest remains in fraud_service and is evaluated in
batches. This live path does NOT fit a machine-learning model for each request.
The legacy FraudPrediction.fraud_probability field stores a *risk score*, not
an estimated/calibrated probability of fraud.
"""
from decimal import Decimal

from django.db.models import Q
from django.utils import timezone

from finance.models import FraudPrediction, Transaction
from .fraud_service import _calculate_behavioural_risk_scores


LIVE_RISK_THRESHOLD = 0.60
LIVE_HISTORY_LIMIT = 250
LIVE_MODEL_VERSION = "BehaviouralRiskHeuristic-v1"


def screen_transaction(transaction):
    """Screen only the new transaction against prior transactions on its account.

    The query is bounded and strictly chronological, including the target
    transaction but not later records. Historic ground-truth anomaly labels
    are never consulted.
    """
    preceding = Q(transaction_time__lt=transaction.transaction_time) | (
        Q(transaction_time=transaction.transaction_time)
        & Q(transaction_id__lte=transaction.transaction_id)
    )
    recent = list(
        Transaction.objects.filter(
            preceding, account_id=transaction.account_id
        ).order_by("-transaction_time", "-transaction_id")[
            : LIVE_HISTORY_LIMIT + 1
        ]
    )
    recent.reverse()
    if not recent or recent[-1].transaction_id != transaction.transaction_id:
        raise ValueError("Transaction is not the latest in its scoring window.")

    score = float(_calculate_behavioural_risk_scores(recent)[-1])
    if not (0 <= score <= 1):
        raise ValueError("Invalid live risk score.")

    prediction, _ = FraudPrediction.objects.update_or_create(
        transaction=transaction,
        defaults={
            "prediction": score >= LIVE_RISK_THRESHOLD,
            "fraud_probability": Decimal(str(round(score, 4))),
            "model_version": LIVE_MODEL_VERSION,
            "predicted_at": timezone.now(),
        },
    )
    return prediction
