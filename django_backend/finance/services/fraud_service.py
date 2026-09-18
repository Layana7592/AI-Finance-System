from collections import Counter, defaultdict, deque
from datetime import timedelta

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


# ============================================================
# STATISTICAL BASELINE
# ============================================================

def statistical_baseline_predictions(transactions):
    """
    Simple statistical baseline.

    Flags transactions whose amount is significantly larger
    than the account's historical median amount.

    This is used as a baseline for comparison with the
    Isolation Forest model.
    """

    if not transactions:
        return np.array([], dtype=int)

    indexed_transactions = list(enumerate(transactions))

    indexed_transactions.sort(
        key=lambda item: (
            item[1].transaction_time is None,
            item[1].transaction_time,
            item[1].transaction_id,
        )
    )

    account_amounts = defaultdict(list)
    predictions = {}

    for original_index, tx in indexed_transactions:

        account_id = tx.account_id
        amount = float(tx.amount or 0.0)

        previous_amounts = account_amounts[account_id]

        prediction = 0

        if len(previous_amounts) >= 5:

            median_amount = float(
                np.median(previous_amounts)
            )

            deviations = np.abs(
                np.array(previous_amounts)
                - median_amount
            )

            mad = float(np.median(deviations))

            robust_scale = 1.4826 * mad

            if robust_scale > 0:

                amount_z = abs(
                    (amount - median_amount)
                    / robust_scale
                )

                if amount_z >= 5:
                    prediction = 1

            else:

                mean_amount = float(
                    np.mean(previous_amounts)
                )

                std_amount = float(
                    np.std(previous_amounts)
                )

                if std_amount > 0:

                    amount_z = abs(
                        (amount - mean_amount)
                        / std_amount
                    )

                    if amount_z >= 5:
                        prediction = 1

        predictions[original_index] = prediction

        account_amounts[account_id].append(amount)

    return np.array(
        [
            predictions[index]
            for index in range(len(transactions))
        ],
        dtype=int,
    )


# ============================================================
# CHRONOLOGICAL FEATURE ENGINEERING
# ============================================================

def _build_chronological_features(transactions):
    """
    Build account-behaviour features using ONLY information
    available before each transaction.

    This prevents future-data leakage.
    """

    if not transactions:
        return np.empty((0, 1)), []

    indexed_transactions = list(
        enumerate(transactions)
    )

    # --------------------------------------------------------
    # Sort chronologically ONLY for feature generation
    # --------------------------------------------------------

    indexed_transactions.sort(
        key=lambda item: (
            item[1].transaction_time is None,
            item[1].transaction_time,
            item[1].transaction_id,
        )
    )

    account_amounts = defaultdict(list)
    account_count = Counter()

    account_merchants = defaultdict(Counter)
    account_locations = defaultdict(Counter)
    account_types = defaultdict(Counter)
    account_hours = defaultdict(Counter)

    previous_transaction_time = {}

    recent_1h = defaultdict(deque)
    recent_24h = defaultdict(deque)

    feature_by_original_index = {}

    for original_index, tx in indexed_transactions:

        account_id = tx.account_id

        amount = float(
            tx.amount or 0.0
        )

        merchant = (
            tx.merchant or "UNKNOWN"
        )

        location = (
            tx.location or "UNKNOWN"
        )

        transaction_type = (
            tx.transaction_type or "UNKNOWN"
        )

        transaction_time = tx.transaction_time

        previous_count = account_count[
            account_id
        ]

        previous_amounts = account_amounts[
            account_id
        ]

        # ----------------------------------------------------
        # ACCOUNT AMOUNT BEHAVIOUR
        # ----------------------------------------------------

        if (
            previous_count >= 5
            and previous_amounts
        ):

            median_amount = float(
                np.median(previous_amounts)
            )

            deviations = np.abs(
                np.array(previous_amounts)
                - median_amount
            )

            mad = float(
                np.median(deviations)
            )

            robust_scale = (
                1.4826 * mad
            )

            if robust_scale > 0:

                amount_deviation = (
                    amount - median_amount
                ) / robust_scale

            else:

                mean_amount = float(
                    np.mean(previous_amounts)
                )

                std_amount = float(
                    np.std(previous_amounts)
                )

                if std_amount > 0:

                    amount_deviation = (
                        amount - mean_amount
                    ) / std_amount

                else:

                    amount_deviation = 0.0

            if median_amount > 0:

                amount_ratio = (
                    amount / median_amount
                )

            else:

                amount_ratio = 1.0

        else:

            amount_deviation = 0.0
            amount_ratio = 1.0

        amount_deviation = float(
            np.clip(
                amount_deviation,
                -20,
                20,
            )
        )

        amount_ratio = float(
            np.clip(
                amount_ratio,
                0,
                50,
            )
        )

        log_amount = float(
            np.log1p(
                max(amount, 0)
            )
        )

        # ----------------------------------------------------
        # MERCHANT BEHAVIOUR
        # ----------------------------------------------------

        merchant_previous_count = (
            account_merchants[
                account_id
            ][merchant]
        )

        if previous_count >= 5:

            merchant_new = (
                1
                if merchant_previous_count == 0
                else 0
            )

            merchant_frequency = (
                merchant_previous_count
                / previous_count
            )

            merchant_rarity = (
                1.0
                - merchant_frequency
            )

        else:

            merchant_new = 0
            merchant_frequency = 0.0
            merchant_rarity = 0.0

        # ----------------------------------------------------
        # LOCATION BEHAVIOUR
        # ----------------------------------------------------

        location_previous_count = (
            account_locations[
                account_id
            ][location]
        )

        if previous_count >= 5:

            location_new = (
                1
                if location_previous_count == 0
                else 0
            )

            location_frequency = (
                location_previous_count
                / previous_count
            )

            location_rarity = (
                1.0
                - location_frequency
            )

        else:

            location_new = 0
            location_frequency = 0.0
            location_rarity = 0.0

        # ----------------------------------------------------
        # TRANSACTION TYPE BEHAVIOUR
        # ----------------------------------------------------

        type_previous_count = (
            account_types[
                account_id
            ][transaction_type]
        )

        if previous_count >= 5:

            type_new = (
                1
                if type_previous_count == 0
                else 0
            )

            type_frequency = (
                type_previous_count
                / previous_count
            )

            type_rarity = (
                1.0
                - type_frequency
            )

        else:

            type_new = 0
            type_frequency = 0.0
            type_rarity = 0.0

        # ----------------------------------------------------
        # TIME-OF-DAY BEHAVIOUR
        # ----------------------------------------------------

        if transaction_time is not None:

            hour = (
                transaction_time.hour
            )

            previous_hour_count = (
                account_hours[
                    account_id
                ][hour]
            )

            if previous_count >= 5:

                unusual_hour = (
                    1
                    if previous_hour_count == 0
                    else 0
                )

                hour_frequency = (
                    previous_hour_count
                    / previous_count
                )

                hour_rarity = (
                    1.0
                    - hour_frequency
                )

            else:

                unusual_hour = 0
                hour_frequency = 0.0
                hour_rarity = 0.0

            hour_sin = np.sin(
                2
                * np.pi
                * hour
                / 24
            )

            hour_cos = np.cos(
                2
                * np.pi
                * hour
                / 24
            )

        else:

            hour = 0
            unusual_hour = 0
            hour_frequency = 0.0
            hour_rarity = 0.0
            hour_sin = 0.0
            hour_cos = 0.0

        # ----------------------------------------------------
        # TIME SINCE PREVIOUS TRANSACTION
        # ----------------------------------------------------

        previous_time = (
            previous_transaction_time.get(
                account_id
            )
        )

        if (
            transaction_time is not None
            and previous_time is not None
        ):

            gap_seconds = max(
                (
                    transaction_time
                    - previous_time
                ).total_seconds(),
                0.0,
            )

            log_gap = float(
                np.log1p(
                    gap_seconds
                )
            )

            short_transaction_gap = (
                1
                if gap_seconds <= 60
                else 0
            )

        else:

            gap_seconds = 86400.0

            log_gap = float(
                np.log1p(
                    gap_seconds
                )
            )

            short_transaction_gap = 0

        # ----------------------------------------------------
        # RECENT FREQUENCY
        # ----------------------------------------------------

        if transaction_time is not None:

            one_hour_queue = (
                recent_1h[account_id]
            )

            while (
                one_hour_queue
                and (
                    transaction_time
                    - one_hour_queue[0]
                )
                > timedelta(hours=1)
            ):

                one_hour_queue.popleft()

            recent_1h_count = len(
                one_hour_queue
            )

            twenty_four_hour_queue = (
                recent_24h[account_id]
            )

            while (
                twenty_four_hour_queue
                and (
                    transaction_time
                    - twenty_four_hour_queue[0]
                )
                > timedelta(hours=24)
            ):

                twenty_four_hour_queue.popleft()

            recent_24h_count = len(
                twenty_four_hour_queue
            )

        else:

            recent_1h_count = 0
            recent_24h_count = 0

        # ----------------------------------------------------
        # ACCOUNT HISTORY
        # ----------------------------------------------------

        account_history_size = float(
            np.log1p(
                previous_count
            )
        )

        # ----------------------------------------------------
        # RICH FEATURE VECTOR
        #
        # IMPORTANT:
        # Raw "amount" is intentionally excluded.
        #
        # Amount behaviour is represented using:
        # log_amount
        # amount_deviation
        # amount_ratio
        # ----------------------------------------------------

        feature_vector = [

            # Amount behaviour
            log_amount,
            amount_deviation,
            amount_ratio,

            # Merchant behaviour
            merchant_new,
            merchant_frequency,
            merchant_rarity,

            # Location behaviour
            location_new,
            location_frequency,
            location_rarity,

            # Transaction type
            type_new,
            type_frequency,
            type_rarity,

            # Time behaviour
            hour_sin,
            hour_cos,
            unusual_hour,
            hour_frequency,
            hour_rarity,

            # Frequency
            recent_1h_count,
            recent_24h_count,

            # Account behaviour
            account_history_size,

            # Transaction gap
            log_gap,
            short_transaction_gap,
        ]

        feature_by_original_index[
            original_index
        ] = feature_vector

        # ----------------------------------------------------
        # UPDATE HISTORY AFTER FEATURE CREATION
        # ----------------------------------------------------

        account_amounts[
            account_id
        ].append(amount)

        account_count[
            account_id
        ] += 1

        account_merchants[
            account_id
        ][merchant] += 1

        account_locations[
            account_id
        ][location] += 1

        account_types[
            account_id
        ][transaction_type] += 1

        if transaction_time is not None:

            account_hours[
                account_id
            ][hour] += 1

            recent_1h[
                account_id
            ].append(
                transaction_time
            )

            recent_24h[
                account_id
            ].append(
                transaction_time
            )

            previous_transaction_time[
                account_id
            ] = transaction_time

    features = [
        feature_by_original_index[index]
        for index in range(len(transactions))
    ]

    return (
        np.array(
            features,
            dtype=float,
        ),
        list(
            range(len(transactions))
        ),
    )


# ============================================================
# BEHAVIOURAL RISK SCORING
# ============================================================

def _calculate_behavioural_risk_scores(
    transactions
):
    """
    Calculate an interpretable behavioural risk score.

    The score combines multiple independent signals:

    - amount deviation
    - new merchant
    - new location
    - unusual transaction type
    - unusual hour
    - recent transaction frequency
    - short transaction gap

    Each signal contributes a controlled amount to the
    final score.
    """

    if not transactions:
        return []

    indexed_transactions = list(
        enumerate(transactions)
    )

    indexed_transactions.sort(
        key=lambda item: (
            item[1].transaction_time is None,
            item[1].transaction_time,
            item[1].transaction_id,
        )
    )

    account_amounts = defaultdict(list)
    account_count = Counter()

    account_merchants = defaultdict(Counter)
    account_locations = defaultdict(Counter)
    account_types = defaultdict(Counter)
    account_hours = defaultdict(Counter)

    previous_transaction_time = {}

    recent_1h = defaultdict(deque)
    recent_24h = defaultdict(deque)

    scores = {}

    for original_index, tx in indexed_transactions:

        account_id = tx.account_id

        amount = float(
            tx.amount or 0.0
        )

        merchant = (
            tx.merchant or "UNKNOWN"
        )

        location = (
            tx.location or "UNKNOWN"
        )

        transaction_type = (
            tx.transaction_type or "UNKNOWN"
        )

        transaction_time = (
            tx.transaction_time
        )

        previous_count = (
            account_count[
                account_id
            ]
        )

        previous_amounts = (
            account_amounts[
                account_id
            ]
        )

        score = 0.0

        # ----------------------------------------------------
        # 1. AMOUNT DEVIATION — 25%
        # ----------------------------------------------------

        if (
            previous_count >= 5
            and previous_amounts
        ):

            median_amount = float(
                np.median(
                    previous_amounts
                )
            )

            deviations = np.abs(
                np.array(
                    previous_amounts
                )
                - median_amount
            )

            mad = float(
                np.median(
                    deviations
                )
            )

            robust_scale = (
                1.4826 * mad
            )

            if robust_scale > 0:

                amount_z = abs(
                    (
                        amount
                        - median_amount
                    )
                    / robust_scale
                )

            else:

                std_amount = float(
                    np.std(
                        previous_amounts
                    )
                )

                if std_amount > 0:

                    amount_z = abs(
                        (
                            amount
                            - np.mean(
                                previous_amounts
                            )
                        )
                        / std_amount
                    )

                else:

                    amount_z = 0.0

            amount_z = min(
                float(amount_z),
                10.0,
            )

            score += (
                min(
                    amount_z / 5.0,
                    1.0,
                )
                * 0.25
            )

        # ----------------------------------------------------
        # 2. NEW MERCHANT — 15%
        # ----------------------------------------------------

        if previous_count >= 5:

            merchant_count = (
                account_merchants[
                    account_id
                ][merchant]
            )

            if merchant_count == 0:
                score += 0.15

        # ----------------------------------------------------
        # 3. NEW LOCATION — 15%
        # ----------------------------------------------------

        if previous_count >= 5:

            location_count = (
                account_locations[
                    account_id
                ][location]
            )

            if location_count == 0:
                score += 0.15

        # ----------------------------------------------------
        # 4. TRANSACTION TYPE — 10%
        # ----------------------------------------------------

        if previous_count >= 5:

            type_count = (
                account_types[
                    account_id
                ][transaction_type]
            )

            if type_count == 0:

                score += 0.10

            else:

                type_frequency = (
                    type_count
                    / previous_count
                )

                if type_frequency < 0.10:
                    score += 0.05

        # ----------------------------------------------------
        # 5. UNUSUAL HOUR — 10%
        # ----------------------------------------------------

        if (
            previous_count >= 5
            and transaction_time is not None
        ):

            hour = (
                transaction_time.hour
            )

            hour_count = (
                account_hours[
                    account_id
                ][hour]
            )

            if hour_count == 0:
                score += 0.10

        # ----------------------------------------------------
        # 6. RECENT 1-HOUR FREQUENCY — 10%
        # ----------------------------------------------------

        if transaction_time is not None:

            one_hour_queue = (
                recent_1h[
                    account_id
                ]
            )

            while (
                one_hour_queue
                and (
                    transaction_time
                    - one_hour_queue[0]
                )
                > timedelta(hours=1)
            ):

                one_hour_queue.popleft()

            recent_1h_count = len(
                one_hour_queue
            )

            if recent_1h_count >= 3:

                score += (
                    min(
                        recent_1h_count / 10.0,
                        1.0,
                    )
                    * 0.10
                )

        # ----------------------------------------------------
        # 7. RECENT 24-HOUR FREQUENCY — 5%
        # ----------------------------------------------------

        if transaction_time is not None:

            twenty_four_hour_queue = (
                recent_24h[
                    account_id
                ]
            )

            while (
                twenty_four_hour_queue
                and (
                    transaction_time
                    - twenty_four_hour_queue[0]
                )
                > timedelta(hours=24)
            ):

                twenty_four_hour_queue.popleft()

            recent_24h_count = len(
                twenty_four_hour_queue
            )

            if recent_24h_count >= 10:

                score += (
                    min(
                        recent_24h_count / 50.0,
                        1.0,
                    )
                    * 0.05
                )

        # ----------------------------------------------------
        # 8. VERY SHORT TRANSACTION GAP — 10%
        # ----------------------------------------------------

        previous_time = (
            previous_transaction_time.get(
                account_id
            )
        )

        if (
            transaction_time is not None
            and previous_time is not None
        ):

            gap_seconds = max(
                (
                    transaction_time
                    - previous_time
                ).total_seconds(),
                0.0,
            )

            if gap_seconds <= 60:

                score += 0.10

            elif gap_seconds <= 300:

                score += 0.05

        scores[
            original_index
        ] = min(
            score,
            1.0,
        )

        # ----------------------------------------------------
        # UPDATE HISTORY
        # ----------------------------------------------------

        account_amounts[
            account_id
        ].append(amount)

        account_count[
            account_id
        ] += 1

        account_merchants[
            account_id
        ][merchant] += 1

        account_locations[
            account_id
        ][location] += 1

        account_types[
            account_id
        ][transaction_type] += 1

        if transaction_time is not None:

            hour = (
                transaction_time.hour
            )

            account_hours[
                account_id
            ][hour] += 1

            recent_1h[
                account_id
            ].append(
                transaction_time
            )

            recent_24h[
                account_id
            ].append(
                transaction_time
            )

            previous_transaction_time[
                account_id
            ] = transaction_time

    return [
        float(
            scores[index]
        )
        for index in range(
            len(transactions)
        )
    ]


# ============================================================
# ISOLATION FOREST
# ============================================================

def isolation_forest_predictions(
    transactions
):
    """
    Hybrid anomaly detection.

    Isolation Forest provides unsupervised anomaly scores.

    Behavioural scoring provides interpretable account-level
    fraud signals.

    The two scores are combined and the top 1% of transactions
    are classified as anomalies.

    Ground-truth labels are NOT used by this function.
    """

    if not transactions:
        return np.array([], dtype=int)

    X, _ = _build_chronological_features(
        transactions
    )

    behavioural_scores = np.array(
        _calculate_behavioural_risk_scores(
            transactions
        ),
        dtype=float,
    )

    isolation_forest = IsolationForest(
        n_estimators=300,
        contamination="auto",
        random_state=42,
        n_jobs=-1,
    )

    isolation_forest.fit(X)

    # Higher value = more anomalous
    isolation_scores = (
        -isolation_forest.decision_function(
            X
        )
    )

    # Convert Isolation Forest scores
    # into percentile ranks from 0 to 1.
    if len(isolation_scores) > 1:

        isolation_percentiles = (
            np.argsort(
                np.argsort(
                    isolation_scores
                )
            )
            / (
                len(isolation_scores)
                - 1
            )
        )

    else:

        isolation_percentiles = (
            np.zeros(
                len(isolation_scores)
            )
        )

    # --------------------------------------------------------
    # HYBRID SCORE
    # --------------------------------------------------------

    hybrid_scores = (
        0.60
        * isolation_percentiles
        + 0.40
        * behavioural_scores
    )

    # --------------------------------------------------------
    # TOP 1% ANOMALY RATE
    # --------------------------------------------------------

    anomaly_count = max(
        1,
        int(
            round(
                len(hybrid_scores)
                * 0.01
            )
        ),
    )

    sorted_indexes = np.argsort(
        hybrid_scores
    )[::-1]

    predictions = np.zeros(
        len(hybrid_scores),
        dtype=int,
    )

    predictions[
        sorted_indexes[
            :anomaly_count
        ]
    ] = 1

    return predictions


# ============================================================
# METRICS
# ============================================================

def calculate_metrics(
    actual,
    predicted,
):
    """
    Calculate classification metrics.
    """

    actual = np.asarray(
        actual,
        dtype=int,
    )

    predicted = np.asarray(
        predicted,
        dtype=int,
    )

    return {
        "precision": round(
            float(
                precision_score(
                    actual,
                    predicted,
                    zero_division=0,
                )
            ),
            4,
        ),
        "recall": round(
            float(
                recall_score(
                    actual,
                    predicted,
                    zero_division=0,
                )
            ),
            4,
        ),
        "f1": round(
            float(
                f1_score(
                    actual,
                    predicted,
                    zero_division=0,
                )
            ),
            4,
        ),
        "accuracy": round(
            float(
                accuracy_score(
                    actual,
                    predicted,
                )
            ),
            4,
        ),
        "confusion_matrix": (
            confusion_matrix(
                actual,
                predicted,
            )
            .tolist()
        ),
    }


# ============================================================
# FRAUD MODEL EVALUATION
# ============================================================

def evaluate_fraud_models(transactions=None):
    """
    Evaluate the statistical baseline and
    Isolation Forest against the synthetic ground-truth
    anomaly labels.

    Ground-truth labels are NOT used when generating
    Isolation Forest predictions.
    """

    if transactions is None:
        from finance.models import Transaction

        transactions = list(
            Transaction.objects.all().order_by(
                "transaction_time",
                "transaction_id",
            )
        )

    if not transactions:
        return {
            "dataset": 0,
            "actual_anomalies": 0,
            "anomaly_percentage": 0.0,
            "statistical_baseline": {},
            "isolation_forest": {},
        }

    # rest of your existing function...
    actual = np.array(
        [
            int(
                tx.is_anomaly
            )
            for tx in transactions
        ],
        dtype=int,
    )

    actual_anomalies = int(
        np.sum(actual)
    )

    anomaly_percentage = (
        actual_anomalies
        / len(transactions)
        * 100
    )

    baseline_predictions = (
        statistical_baseline_predictions(
            transactions
        )
    )

    isolation_predictions = (
        isolation_forest_predictions(
            transactions
        )
    )

    return {
        "dataset": len(
            transactions
        ),
        "actual_anomalies": (
            actual_anomalies
        ),
        "anomaly_percentage": round(
            anomaly_percentage,
            4,
        ),
        "statistical_baseline": (
            calculate_metrics(
                actual,
                baseline_predictions,
            )
        ),
        "isolation_forest": (
            calculate_metrics(
                actual,
                isolation_predictions,
            )
        ),
    }


# ============================================================
# SAVE FRAUD PREDICTIONS
# ============================================================

def generate_fraud_predictions(transactions=None):
    """
    Generate and save fraud predictions.

    The model does not use is_anomaly while generating
    predictions.

    is_anomaly is only the synthetic ground truth used
    separately for evaluation.
    """

    from decimal import Decimal
    from django.utils import timezone
    from finance.models import Transaction, FraudPrediction

    if transactions is None:
        transactions = list(
            Transaction.objects.all().order_by(
                "transaction_time",
                "transaction_id",
            )
        )

    if not transactions:
        return 0

    predictions = isolation_forest_predictions(
        transactions
    )

    created_count = 0

    for index, tx in enumerate(transactions):

        prediction = int(predictions[index])

        # Convert Isolation Forest output:
        # -1 = anomaly/fraud
        #  1 = normal
        is_fraud = prediction == 1

        # Use the behavioural + Isolation Forest result
        # as a simple probability-like score for storage.
        fraud_probability = Decimal(
            "1.0" if is_fraud else "0.0"
        )

        FraudPrediction.objects.update_or_create(
            transaction=tx,
            defaults={
                "prediction": is_fraud,
                "fraud_probability": fraud_probability,
                "model_version": "IsolationForest-v2",
                "predicted_at": timezone.now(),
            },
        )

        created_count += 1

    return created_count