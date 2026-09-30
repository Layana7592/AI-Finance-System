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


from rest_framework import serializers
from django.utils import timezone

from .models import Account, Transaction


class AccountSerializer(serializers.ModelSerializer):

    account_id = serializers.IntegerField(read_only=True)
    balance = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True
    )
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Account
        fields = [
            "account_id",
            "user",
            "account_number",
            "account_type",
            "balance",
            "created_at",
        ]

    def validate_user(self, value):
        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError(
                "Authentication is required."
            )

        user = request.user
        role = getattr(
            getattr(user, "role", None),
            "role_name",
            None
        )

        if role == "Admin":
            return value

        if role == "Manager":
            if value.branch_id != user.branch_id:
                raise serializers.ValidationError(
                    "You can only create accounts for users "
                    "in your own branch."
                )
            return value

        raise serializers.ValidationError(
            "You are not allowed to create accounts."
        )

    def create(self, validated_data):
        validated_data["balance"] = 0
        validated_data["created_at"] = timezone.now()

        return super().create(validated_data)


class TransactionSerializer(serializers.ModelSerializer):

    transaction_id = serializers.IntegerField(read_only=True)
    is_anomaly = serializers.IntegerField(read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "transaction_id",
            "account",
            "amount",
            "transaction_type",
            "merchant",
            "location",
            "transaction_time",
            "status",
            "is_anomaly",
        ]

    def validate_account(self, value):
        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError(
                "Authentication is required."
            )

        user = request.user
        role = getattr(
            getattr(user, "role", None),
            "role_name",
            None
        )

        if role == "Admin":
            return value

        if role == "Manager":
            if value.user.branch_id != user.branch_id:
                raise serializers.ValidationError(
                    "You can only access accounts "
                    "in your own branch."
                )
            return value

        raise serializers.ValidationError(
            "You are not allowed to create transactions."
        )

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Transaction amount must be greater than zero."
            )

        return value
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