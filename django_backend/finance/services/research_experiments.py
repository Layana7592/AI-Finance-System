"""Additional controlled fraud studies — never overwrite the legacy benchmark.

Study A: train Isolation Forest only on chronologically earlier transactions
         and evaluate on a later period. Features are causal (account history
         before each event); scoring uses the frozen fitted model and threshold.

Study B: separately generate stable amount distributions with behavioural
         novelty/bursts and test by time. This is STILL synthetic.
"""
from collections import Counter
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import numpy as np
from sklearn.ensemble import IsolationForest

from .fraud_service import (
    _build_chronological_features,
    calculate_metrics,
    statistical_baseline_predictions,
)

FEATURE_NAMES = (
    "log_amount", "amount_deviation", "amount_ratio",
    "merchant_new", "merchant_frequency", "merchant_rarity",
    "location_new", "location_frequency", "location_rarity",
    "transaction_type_new", "transaction_type_frequency", "transaction_type_rarity",
    "hour_sin", "hour_cos", "day_sin", "day_cos",
    "unusual_hour", "hour_frequency", "hour_rarity",
    "recent_1h_count", "recent_24h_count",
    "account_history_size", "log_gap", "short_transaction_gap",
)
ANOMALY_TYPES = ("new_merchant_and_location", "night_and_type_change", "rapid_repeat")


def generate_behavioural_study(seed=42, accounts=60, transactions=6000, anomalies=90):
    """Produce a separate deterministic, time-ordered dataset.

    Anomaly cases begin only in the final 20% of the period and are paired
    with otherwise ordinary amounts. Every account has habitual merchant,
    location, daytime activity and transaction type; labelled exceptions
    alter *behaviour* instead of multiplying transaction amounts.

    The study is intentionally synthetic: no real fraud claims and no
    guarantee a novelty event is malicious.
    """
    if accounts < 5 or transactions < 250 or not 0 < anomalies <= transactions // 10:
        raise ValueError("Use >=5 accounts, >=250 rows and anomaly prevalence <=10%.")
    rng = np.random.default_rng(seed)
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    rows = []
    test_start = int(transactions * 0.8)
    available = np.arange(test_start + 10, transactions - 10)
    if anomalies > len(available):
        raise ValueError("Not enough test rows to place anomalies.")
    positions = set(map(int, rng.choice(available, size=anomalies, replace=False)))
    categories = {}
    normal_values = {}

    # Account-specific but comparable monetary patterns, independent of label.
    for a in range(accounts):
        normal_values[a] = float(rng.uniform(350, 1500))

    for index in range(transactions):
        account_id = (index % accounts) + 1
        a = account_id - 1
        # One global timeline with regular account visits, so a burst can be
        # unambiguously recognised without using a label as a feature.
        day = index // (accounts * 2)
        visit = (index // accounts) % 2
        normal_time = start + timedelta(days=day, hours=10 + 4 * visit, minutes=(a % 6) * 5)
        transaction_time = normal_time
        merchant = f"RegularMerchant-{a % 3}"
        location = f"UsualCity-{a % 4}"
        transaction_type = "Purchase"
        amount = float(np.clip(rng.lognormal(np.log(normal_values[a]), 0.14), 50, 9500))
        is_anomaly = int(index in positions)
        category = "normal"
        if is_anomaly:
            category = ANOMALY_TYPES[len(categories) % len(ANOMALY_TYPES)]
            if category == "new_merchant_and_location":
                merchant = f"UnrecognisedMerchant-{index}"
                location = f"UnexpectedCity-{index}"
            elif category == "night_and_type_change":
                transaction_time = normal_time.replace(hour=2)
                transaction_type = "Withdrawal"
                location = f"UnexpectedCity-{index}"
            else:
                # Same monetary distribution; place a repeat just five
                # seconds after the earlier regular activity of the account.
                # This creates a short-gap/velocity anomaly, not four
                # invented events. Its time is still strictly after a
                # previously known record for the same account.
                previous_visit = (
                    normal_time - timedelta(hours=4)
                    if visit == 1
                    else normal_time - timedelta(days=1, hours=-4)
                )
                transaction_time = previous_visit + timedelta(seconds=5)
                merchant = f"RapidMerchant-{a % 3}"
        rows.append(SimpleNamespace(
            transaction_id=index + 1, account_id=account_id,
            amount=Decimal(f"{amount:.2f}"),
            merchant=merchant, location=location,
            transaction_type=transaction_type,
            transaction_time=transaction_time,
            is_anomaly=is_anomaly, anomaly_kind=category,
        ))
        if is_anomaly:
            categories[index + 1] = category

    # Sorting is done by the exact same stable key as in the production
    # feature builder; preserve generated IDs for traceability.
    rows.sort(key=lambda x: (x.transaction_time, x.transaction_id))
    return rows


def _round_metrics(metric):
    return {key: value for key, value in metric.items()}


def _error_cases(transactions, labels, pred, scores, max_cases=8):
    groups = {"false_positive": [], "false_negative": [], "true_positive": []}
    for tx, truth, prediction, score in zip(transactions, labels, pred, scores):
        label = (
            "false_positive" if prediction and not truth else
            "false_negative" if truth and not prediction else
            "true_positive" if truth and prediction else None
        )
        if label and len(groups[label]) < max_cases:
            groups[label].append({
                "transaction_id": int(tx.transaction_id),
                "time": tx.transaction_time.isoformat(),
                "amount": round(float(tx.amount), 2),
                "merchant": tx.merchant,
                "location": tx.location,
                "transaction_type": tx.transaction_type,
                "known_synthetic_anomaly_type": getattr(tx, "anomaly_kind", "not recorded"),
                "anomaly_score": round(float(score), 5),
            })
    return groups


def _descriptive_feature_differences(features, actual, max_features=8):
    """Descriptive rank by standardized difference; labels used only AFTER fitting.

    NOT trained feature importance, not a causal explanation or proof that a
    feature determines a prediction.
    """
    positive = features[actual == 1]
    negative = features[actual == 0]
    if len(positive) == 0 or len(negative) == 0:
        return []
    output = []
    for j, name in enumerate(FEATURE_NAMES):
        p = float(np.median(positive[:, j]))
        n = float(np.median(negative[:, j]))
        spread = float(np.std(features[:, j]))
        magnitude = abs(p - n) / (spread + 1e-9)
        output.append((magnitude, {
            "feature": name,
            "anomaly_median": round(p, 4),
            "normal_median": round(n, 4),
            "standardized_median_difference": round(magnitude, 4),
        }))
    return [x[1] for x in sorted(output, reverse=True, key=lambda x: x[0])[:max_features]]


def evaluate_chronological_holdout(transactions, test_fraction=0.2, seed=42,
                                    estimators=160, contamination=0.01):
    """Fit on earlier transactions; evaluate on strictly later observations.

    No labels are supplied to the estimator, and contamination is pre-set,
    not tuned against held-out labels. The entire time-ordered history is
    feature-engineered causally to permit each later event to see earlier
    transactions as it would online. No future event affects past features.
    """
    if not 0.05 <= test_fraction <= 0.5:
        raise ValueError("test_fraction must be between 0.05 and 0.5.")
    if not 0 < contamination < 0.5:
        raise ValueError("contamination must be between zero and 0.5.")
    if not 10 <= estimators <= 500:
        raise ValueError("estimators must be between 10 and 500.")
    if len(transactions) < 100:
        raise ValueError("Need at least 100 observations for time holdout.")
    if any(tx.transaction_time is None for tx in transactions):
        raise ValueError("Chronological study requires transaction timestamps.")

    rows = sorted(transactions, key=lambda t: (t.transaction_time, t.transaction_id))
    split = int(round(len(rows) * (1 - test_fraction)))
    split = min(max(split, 50), len(rows) - 20)
    train, test = rows[:split], rows[split:]
    if train[-1].transaction_time >= test[0].transaction_time:
        raise ValueError("Training and test timestamp ranges overlap; adjust time split.")

    all_features, _ = _build_chronological_features(rows)
    if all_features.shape != (len(rows), len(FEATURE_NAMES)):
        raise ValueError("Chronological feature schema changed; review benchmark.")
    if not np.isfinite(all_features).all():
        raise ValueError("Non-finite feature encountered.")
    x_train, x_test = all_features[:split], all_features[split:]

    model = IsolationForest(
        n_estimators=estimators,
        contamination=contamination,
        random_state=seed,
        n_jobs=-1,
    )
    model.fit(x_train)  # NEVER fit to test rows.
    scores = -model.decision_function(x_test)
    predictions = (model.predict(x_test) == -1).astype(int)
    actual = np.array([int(row.is_anomaly) for row in test], dtype=int)
    baseline = statistical_baseline_predictions(rows)[split:]

    tp = int(np.sum((actual == 1) & (predictions == 1)))
    fn = int(np.sum((actual == 1) & (predictions == 0)))
    fp = int(np.sum((actual == 0) & (predictions == 1)))
    tn = int(np.sum((actual == 0) & (predictions == 0)))

    return {
        "method": "Chronological 80/20 holdout with causal history; Isolation Forest fitted on training only",
        "source": "controlled synthetic transactions",
        "train_rows": len(train),
        "test_rows": len(test),
        "training_end": train[-1].transaction_time.isoformat(),
        "test_start": test[0].transaction_time.isoformat(),
        "test_end": test[-1].transaction_time.isoformat(),
        "test_anomalies": int(actual.sum()),
        "test_anomaly_prevalence_pct": round(100 * float(np.mean(actual)), 3),
        "seed": seed,
        "contamination_assumption": contamination,
        "estimators": estimators,
        "features": list(FEATURE_NAMES),
        "isolation_forest": _round_metrics(calculate_metrics(actual, predictions)),
        "statistical_baseline": _round_metrics(calculate_metrics(actual, baseline)),
        "confusion_counts": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
        "false_alerts_per_100_test_transactions": round(100 * fp / len(test), 3),
        "missed_anomaly_rate": round(fn / int(actual.sum()), 4) if actual.sum() else None,
        "cases": _error_cases(test, actual, predictions, scores),
        "descriptive_feature_differences": _descriptive_feature_differences(
            x_test, actual
        ),
        "known_limitations": [
            "Synthetic labels are an artificial benchmark, not confirmed fraud.",
            "No labels or future transaction features are used for fitting.",
            "Causal features incorporate earlier test-period events at prediction time.",
            "The 1% contamination is a prespecified assumption, not a calibrated fraud risk.",
            "Descriptive feature contrasts are not causal or fitted feature importance.",
        ],
    }


def evaluate_behavioural_study(seed=42, accounts=60, transactions=6000, anomalies=90,
                                estimators=160):
    sample = generate_behavioural_study(
        seed=seed, accounts=accounts, transactions=transactions, anomalies=anomalies
    )
    report = evaluate_chronological_holdout(
        sample, test_fraction=0.2, seed=seed, estimators=estimators
    )
    kinds = Counter(
        tx.anomaly_kind for tx in sample
        if tx.is_anomaly
    )
    report["scenario"] = "Behaviour-only anomalies; no anomaly-triggered amount inflation"
    report["anomaly_type_counts"] = dict(sorted(kinds.items()))
    report["amount_distribution"] = {
        "normal_median": round(float(np.median([
            float(tx.amount) for tx in sample if not tx.is_anomaly
        ])), 2),
        "anomaly_median": round(float(np.median([
            float(tx.amount) for tx in sample if tx.is_anomaly
        ])), 2),
    }
    return report
