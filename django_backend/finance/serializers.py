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
    """
    Serializer for displaying user information.

    Password and password hash are NEVER exposed.
    """

    class Meta:
        model = User
        fields = [
            "user_id",
            "username",
            "email",
            "created_at",
            "role",
            "branch",
        ]
        read_only_fields = [
            "user_id",
            "created_at",
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating users.

    Accepts a plain password as write-only input
    and stores it using Django's password hashing.
    """

    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
    )

    class Meta:
        model = User
        fields = [
            "user_id",
            "username",
            "email",
            "password",
            "role",
            "branch",
        ]
        read_only_fields = [
            "user_id",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        return user


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