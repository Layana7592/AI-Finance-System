
from rest_framework import serializers

from .models import (
    Role,
    Branch,
    User,
    Account,
    Transaction,
    FraudPrediction,
    FinancialForecast,
    AuditLog,
    Alert,
    JournalEntry,
)


# ==================================================
# ROLE
# ==================================================

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = "__all__"


# ==================================================
# BRANCH
# ==================================================

class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = "__all__"


# ==================================================
# USER
# ==================================================

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"


# ==================================================
# ACCOUNT
# ==================================================

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = "__all__"


# ==================================================
# TRANSACTION
# ==================================================

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"


# ==================================================
# FRAUD PREDICTION
# ==================================================

class FraudPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FraudPrediction
        fields = "__all__"


# ==================================================
# FINANCIAL FORECAST
# ==================================================

class FinancialForecastSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialForecast
        fields = "__all__"


# ==================================================
# AUDIT LOG
# ==================================================

class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = "__all__"


# ==================================================
# ALERT
# ==================================================

class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = "__all__"


# ==================================================
# JOURNAL ENTRY
# ==================================================

class JournalEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalEntry
        fields = "__all__"

