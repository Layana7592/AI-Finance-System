from decimal import Decimal
from django.utils import timezone
from django.db import transaction as db_transaction

from finance.models import Transaction, FraudPrediction


def generate_fraud_predictions():
    """
    Generate fraud predictions for transactions.

    Current version:
    - Uses transaction amount as a simple baseline signal.
    - Transactions with unusually high amounts are flagged.
    - Saves predictions into fraud_predictions table.
    """

    transactions = Transaction.objects.all().order_by("transaction_id")

    if not transactions.exists():
        return []

    results = []

    # Get transaction amounts
    amounts = [
        float(t.amount)
        for t in transactions
        if t.amount is not None
    ]

    if not amounts:
        return []

    # Simple statistical threshold
    mean_amount = sum(amounts) / len(amounts)

    variance = sum(
        (amount - mean_amount) ** 2
        for amount in amounts
    ) / len(amounts)

    std_amount = variance ** 0.5

    # Transactions above mean + 3 standard deviations
    threshold = mean_amount + (3 * std_amount)

    with db_transaction.atomic():

        # Remove previous predictions
        FraudPrediction.objects.all().delete()

        for txn in transactions:

            amount = float(txn.amount or 0)

            # Fraud probability
            if amount > threshold:
                fraud_probability = 0.95
                is_fraud = True

            elif amount > mean_amount + (2 * std_amount):
                fraud_probability = 0.75
                is_fraud = True

            else:
                fraud_probability = 0.05
                is_fraud = False

            prediction = FraudPrediction.objects.create(
                transaction=txn,
                fraud_probability=Decimal(
                    str(round(fraud_probability, 4))
                ),
                prediction=is_fraud,
                model_version="baseline-v1",
                predicted_at=timezone.now()
            )

            results.append({
                "prediction_id": prediction.prediction_id,
                "transaction_id": txn.transaction_id,
                "fraud_probability": float(
                    prediction.fraud_probability
                ),
                "prediction": prediction.prediction,
                "model_version": prediction.model_version,
                "predicted_at": prediction.predicted_at.isoformat()
            })

    return results