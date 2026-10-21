"""Cache *expensive research evaluations*, not mutable operational facts.

The dashboard and report continue to query transaction counts, balances,
monthly aggregates, forecast rows and current alerts as appropriate.
Re-training an Isolation Forest and refitting SARIMA at every page load is
unacceptable. Cache the paired research evaluation per verifiable, append-only
synthetic dataset fingerprint with bounded TTL. Supports shared Django cache
backends; default local-memory cache is only shared within one worker.
"""
from hashlib import sha256
import json

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.db.models import Count, Max, Min, Sum

from finance.models import Transaction
from .research_scope import RESEARCH_SCOPE_VERSION, research_transactions
from finance.services.fraud_service import evaluate_fraud_models
from finance.services.forecast_service import evaluate_forecast_models


CACHE_SCHEMA = "research-v5-frozen-2024-2025"


def research_dataset_fingerprint():
    """Cheap DB aggregate: no model fit or full Python row deserialization.

    Operations outside the frozen 2024–2025 study do NOT invalidate its
    model metrics. For deliberate raw SQL or bulk in-place edits within
    the study period, TTL still bounds stale report risk.
    Different databases and differing amount/label sums get different keys.
    """
    aggregate = research_transactions(Transaction.objects.all()).aggregate(
        total=Count("transaction_id"),
        first=Min("transaction_id"),
        latest=Max("transaction_id"),
        amount_sum=Sum("amount"),
        anomalies=Sum("is_anomaly"),
        earliest_time=Min("transaction_time"),
        latest_time=Max("transaction_time"),
    )
    identity = {
        "db_alias": connection.alias,
        "db_name": str(connection.settings_dict.get("NAME")),
        "total": aggregate["total"],
        "first": aggregate["first"],
        "latest": aggregate["latest"],
        "amount_sum": str(aggregate["amount_sum"]),
        "anomalies": aggregate["anomalies"],
        "earliest_time": str(aggregate["earliest_time"]),
        "latest_time": str(aggregate["latest_time"]),
        "schema": CACHE_SCHEMA,
        "study_scope": RESEARCH_SCOPE_VERSION,
    }
    data = json.dumps(identity, sort_keys=True)
    digest = sha256(data.encode("utf-8")).hexdigest()
    return "finance:research:" + digest


def get_cached_research_evaluations():
    """Return deterministic model metrics with cache metadata.

    No exceptions or failed partial results are cached. Reads against the
    same synthetic dataset can reuse expensive model evaluations. The
    cache TTL and returned provenance prevent a false live-fit claim.
    """
    key = research_dataset_fingerprint()
    cached = cache.get(key)
    if cached is not None:
        return {
            "fraud_evaluation": cached["fraud_evaluation"],
            "forecast_evaluation": cached["forecast_evaluation"],
            "cache": {"hit": True, "schema": CACHE_SCHEMA},
        }

    fraud = evaluate_fraud_models()
    forecast = evaluate_forecast_models()
    result = {"fraud_evaluation": fraud, "forecast_evaluation": forecast}
    seconds = int(getattr(settings, "RESEARCH_EVAL_CACHE_SECONDS", 900))
    if seconds > 0:
        cache.set(key, result, timeout=min(seconds, 3600))
    return {**result, "cache": {"hit": False, "schema": CACHE_SCHEMA}}
