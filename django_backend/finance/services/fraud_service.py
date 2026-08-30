from decimal import Decimal

import numpy as np

from django.db import transaction as db_transaction
from django.utils import timezone
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from finance.models import Transaction, FraudPrediction


# ============================================================
# STATISTICAL BASELINE
# ============================================================

def statistical_baseline_predictions(transactions):
    """
    Statistical anomaly baseline using:
        threshold = mean + 3 * standard deviation

    Returns:
        numpy array of 0/1 predictions.
    """

    amounts = np.array(
        [
            float(txn.amount)
            for txn in transactions
            if txn.amount is not None
        ],
        dtype=float,
    )

    if len(amounts) == 0:
        return np.array([], dtype=int)

    mean_amount = np.mean(amounts)
    std_amount = np.std(amounts)

    threshold = mean_amount + (3 * std_amount)

    predictions = (
        amounts > threshold
    ).astype(int)

    return predictions


# ============================================================
# ISOLATION FOREST
# ============================================================

def isolation_forest_predictions(transactions):
    """
    Isolation Forest anomaly detection.

    Since the dataset contains approximately 1% anomalies,
    contamination is set to 0.01.

    Uses transaction amount as the primary numerical feature.
    """

    amounts = np.array(
        [
            float(txn.amount or 0)
            for txn in transactions
        ],
        dtype=float,
    )

    if len(amounts) == 0:
        return np.array([], dtype=int)

    # Reshape for sklearn: one feature = transaction amount
    X = amounts.reshape(-1, 1)

    model = IsolationForest(
        n_estimators=200,
        contamination=0.01,
        random_state=42,
        n_jobs=-1,
    )

    predictions = model.fit_predict(X)

    # Isolation Forest:
    #  1  = normal
    # -1  = anomaly
    anomaly_predictions = (
        predictions == -1
    ).astype(int)

    return anomaly_predictions


# ============================================================
# MODEL EVALUATION
# ============================================================

def calculate_metrics(y_true, y_pred):
    """
    Calculate classification metrics for anomaly detection.
    """

    precision = precision_score(
        y_true,
        y_pred,
        zero_division=0,
    )

    recall = recall_score(
        y_true,
        y_pred,
        zero_division=0,
    )

    f1 = f1_score(
        y_true,
        y_pred,
        zero_division=0,
    )

    matrix = confusion_matrix(
        y_true,
        y_pred,
        labels=[0, 1],
    )

    return {
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1_score": round(float(f1), 4),
        "confusion_matrix": matrix.tolist(),
    }


# ============================================================
# COMPARE BASELINE VS ISOLATION FOREST
# ============================================================

def evaluate_fraud_models():
    """
    Compare:

        1. Statistical baseline
        2. Isolation Forest

    against the verified Transaction.is_anomaly ground truth.

    Returns a dictionary containing:
        - dataset size
        - actual anomaly count
        - anomaly percentage
        - baseline metrics
        - Isolation Forest metrics
    """

    transactions = list(
        Transaction.objects
        .all()
        .order_by("transaction_id")
    )

    if not transactions:
        return {
            "dataset": {
                "transactions": 0,
                "actual_anomalies": 0,
                "anomaly_percentage": 0.0,
            },
            "statistical_baseline": calculate_metrics(
                np.array([], dtype=int),
                np.array([], dtype=int),
            ),
            "isolation_forest": calculate_metrics(
                np.array([], dtype=int),
                np.array([], dtype=int),
            ),
        }

    # Ground truth
    y_true = np.array(
        [
            1 if txn.is_anomaly == 1 else 0
            for txn in transactions
        ],
        dtype=int,
    )

    # Statistical baseline
    baseline_predictions = (
        statistical_baseline_predictions(
            transactions
        )
    )

    # Isolation Forest
    isolation_predictions = (
        isolation_forest_predictions(
            transactions
        )
    )

    actual_anomalies = int(
        np.sum(y_true)
    )

    total_transactions = len(
        transactions
    )

    anomaly_percentage = (
        actual_anomalies
        / total_transactions
        * 100
    )

    return {
        "dataset": {
            "transactions": total_transactions,
            "actual_anomalies": actual_anomalies,
            "anomaly_percentage": round(
                anomaly_percentage,
                2,
            ),
        },

        "statistical_baseline": (
            calculate_metrics(
                y_true,
                baseline_predictions,
            )
        ),

        "isolation_forest": (
            calculate_metrics(
                y_true,
                isolation_predictions,
            )
        ),
    }


# ============================================================
# GENERATE FRAUD PREDICTIONS
# ============================================================

def generate_fraud_predictions():
    """
    Generate fraud predictions and save them to the
    fraud_predictions table.

    The saved predictions use the statistical baseline,
    preserving the existing API behaviour.

    Isolation Forest is evaluated separately through
    evaluate_fraud_models().
    """

    transactions = list(
        Transaction.objects
        .all()
        .order_by("transaction_id")
    )

    if not transactions:
        return []

    amounts = [
        float(txn.amount)
        for txn in transactions
        if txn.amount is not None
    ]

    if not amounts:
        return []

    # --------------------------------------------------------
    # Statistical baseline
    # --------------------------------------------------------

    mean_amount = sum(amounts) / len(amounts)

    variance = sum(
        (amount - mean_amount) ** 2
        for amount in amounts
    ) / len(amounts)

    std_amount = variance ** 0.5

    threshold = (
        mean_amount
        + (3 * std_amount)
    )

    results = []

    with db_transaction.atomic():

        # Remove previous predictions
        FraudPrediction.objects.all().delete()

        for txn in transactions:

            amount = float(
                txn.amount or 0
            )

            # ----------------------------------------------
            # Fraud probability
            # ----------------------------------------------

            if amount > threshold:

                fraud_probability = 0.95
                is_fraud = True

            elif amount > (
                mean_amount
                + (2 * std_amount)
            ):

                fraud_probability = 0.75
                is_fraud = True

            else:

                fraud_probability = 0.05
                is_fraud = False

            prediction = (
                FraudPrediction.objects.create(
                    transaction=txn,
                    fraud_probability=Decimal(
                        str(
                            round(
                                fraud_probability,
                                4,
                            )
                        )
                    ),
                    prediction=is_fraud,
                    model_version="baseline-v1",
                    predicted_at=timezone.now(),
                )
            )

            results.append({
                "prediction_id": (
                    prediction.prediction_id
                ),
                "transaction_id": (
                    txn.transaction_id
                ),
                "fraud_probability": float(
                    prediction.fraud_probability
                ),
                "prediction": (
                    prediction.prediction
                ),
                "model_version": (
                    prediction.model_version
                ),
                "predicted_at": (
                    prediction.predicted_at.isoformat()
                ),
            })

    return results