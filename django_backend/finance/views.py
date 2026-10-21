from rest_framework import status, viewsets
from rest_framework.response import Response
from .serializers import UserSerializer, UserCreateSerializer
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from .permissions import IsAdminOrManager, IsAdminManagerOrAnalyst, IsAdminOrAnalyst, IsAdmin
from .permissions import IsAdminOrManagerForWrite
from .permissions import IsAdminOrManagerForWriteAlerts
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied, ValidationError, MethodNotAllowed
from django.utils import timezone
from django.db import transaction as db_transaction
from .services.live_fraud_service import screen_transaction
from .services.audit_service import create_audit_log


from .models import (
    User,
    Role,
    Account,
    Transaction,
    FraudPrediction,
    FinancialForecast,
    AuditLog,
    Alert,
    JournalEntry,
)

from .serializers import (
    UserSerializer,
    AccountSerializer,
    TransactionSerializer,
    FraudPredictionSerializer,
    FinancialForecastSerializer,
    AuditLogSerializer,
    AlertSerializer,
    JournalEntrySerializer,
)

from .services.fraud_service import evaluate_fraud_models
from .services.forecast_service import evaluate_forecast_models
from .services.dashboard_service import get_dashboard_data
from .services.gemini_service import generate_gemini_report


# ============================================================
# USER VIEWSET
# ============================================================

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrManager]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    def get_queryset(self):
        user = self.request.user

        # Admin can see all users
        if user.role.role_name == "Admin":
            return User.objects.all().order_by("user_id")

        # Manager can only see users from their own branch
        if user.role.role_name == "Manager":
            return User.objects.filter(
                branch=user.branch
            ).order_by("user_id")

        return User.objects.none()

    def perform_create(self, serializer):
        user = self.request.user

        # Admin can create users normally
        if user.role.role_name == "Admin":
            created_user = serializer.save()
        else:
            # Manager can create users only in their own branch
            # and cannot create another Admin/Manager account.
    
            customer_role = Role.objects.get(role_name="Customer")

            created_user = serializer.save(
                role=customer_role,
                branch=user.branch,
            )

        create_audit_log(
            self.request,
            (
                f"User {created_user.user_id} created by "
                f"User {user.user_id}."
            ),
        )

    def perform_update(self, serializer):
        user = self.request.user

        # Admin can update users normally
        if user.role.role_name == "Admin":
            updated_user = serializer.save()
        else:
            target_user = self.get_object()

            # Manager can only modify users in their own branch
            if target_user.branch != user.branch:
                raise PermissionDenied(
                    "You can only modify users in your own branch."
                )

            # Manager cannot change the user role or branch
            updated_user = serializer.save(
                role=target_user.role,
                branch=target_user.branch,
            )

        create_audit_log(
            self.request,
            (
                f"User {updated_user.user_id} updated by "
                f"User {user.user_id}."
            ),
        )

# ============================================================
# ACCOUNT
# ============================================================

class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer
    permission_classes = [IsAdminOrManagerForWrite]

    def get_queryset(self):
        user = self.request.user

        if user.role.role_name == "Admin":
            return Account.objects.all().order_by("-account_id")

        if user.role.role_name == "Manager":
            return Account.objects.filter(
                user__branch=user.branch
            ).order_by("-account_id")

        if user.role.role_name == "Analyst":
            return Account.objects.all().order_by("-account_id")

        if user.role.role_name == "Customer":
            return Account.objects.filter(
                user=user
            ).order_by("-account_id")

        return Account.objects.none()
    def perform_create(self, serializer):
        account = serializer.save()

        create_audit_log(
            self.request,
            (
                f"Account {account.account_id} created by "
                f"User {self.request.user.user_id}."
            ),
        )

    def perform_update(self, serializer):
        account = serializer.save()

        create_audit_log(
            self.request,
            (
                f"Account {account.account_id} updated by "
                f"User {self.request.user.user_id}."
            ),
        )


    def perform_destroy(self, instance):
        account_id = instance.account_id

        instance.delete()

        create_audit_log(
            self.request,
            (
                f"Account {account_id} deleted by "
                f"User {self.request.user.user_id}."
            ),
        )

# ============================================================
# TRANSACTION
# ============================================================

class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAdminOrManagerForWrite]
    # Preserve original transactions and their audit trail; no in-place edits/deletes.
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        user = self.request.user

        # Admin → can access all transactions
        if user.role.role_name == "Admin":
            return Transaction.objects.all().order_by("-transaction_id")

        # Manager → can access transactions from their branch
        if user.role.role_name == "Manager":
            return Transaction.objects.filter(
                account__user__branch=user.branch
            ).order_by("-transaction_id")

        # Customer → can access only their own transactions
        if user.role.role_name == "Customer":
            return Transaction.objects.filter(
                account__user=user
            ).order_by("-transaction_id")

        # Analyst → can read all transactions
        if user.role.role_name == "Analyst":
            return Transaction.objects.all().order_by("-transaction_id")

        # Any unknown role → no access
        return Transaction.objects.none()

    @db_transaction.atomic
    def perform_create(self, serializer):
        # A transaction, its score, alert (if any) and audit log commit together.
        transaction = serializer.save()

        # Account-bounded behavioural screen; Isolation Forest is a batch benchmark.
        prediction = screen_transaction(transaction)

        if prediction.prediction:
            Alert.objects.get_or_create(
                transaction=transaction,
                alert_type="Fraud / Anomaly",
                defaults={
                    "severity": "High",
                    "message": (
                        f"Transaction {transaction.transaction_id} "
                        f"was flagged by {prediction.model_version}."
                    ),
                    "is_resolved": False,
                    "created_at": timezone.now(),
                },
            )

        create_audit_log(
            self.request,
            (
                f"Transaction {transaction.transaction_id} created and screened. "
                f"Model: {prediction.model_version}. "
                f"Flagged: {prediction.prediction}."
            ),
        )


# ============================================================
# FRAUD / ANOMALY PREDICTION
# ============================================================

class FraudPredictionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FraudPrediction.objects.all()
    serializer_class = FraudPredictionSerializer
    permission_classes = [IsAdminManagerOrAnalyst]

    def get_queryset(self):
        user = self.request.user

        if user.role.role_name == "Admin":
            return FraudPrediction.objects.all().order_by(
                "-prediction_id"
            )

        if user.role.role_name == "Manager":
            return FraudPrediction.objects.filter(
                transaction__account__user__branch=user.branch
            ).order_by("-prediction_id")

        if user.role.role_name == "Analyst":
            return FraudPrediction.objects.all().order_by(
                "-prediction_id"
            )

        return FraudPrediction.objects.none()        
## ============================================================
# FINANCIAL FORECAST
# ============================================================

class FinancialForecastViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = FinancialForecast.objects.all().order_by("forecast_month")
    serializer_class = FinancialForecastSerializer
    permission_classes = [IsAdminOrAnalyst]

    # other methods...

    @action(
        detail=False,
        methods=["post"],
        url_path="generate",
        permission_classes=[IsAdmin],
    )

    def generate(self, request):
        """
        Generate and save future financial forecasts.
        """

        horizon = request.data.get("horizon", 12)

        try:
            horizon = int(horizon)

            if horizon <= 0 or horizon > 24:
                return Response(
                    {"error": "Horizon must be between 1 and 24 months."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except (TypeError, ValueError):
            return Response(
                {"error": "Horizon must be an integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from django.utils import timezone
            from .services.forecast_service import generate_forecast

            forecasts = generate_forecast(horizon)

            if not forecasts:
                return Response(
                    {"error": "No forecast data available."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Do not delete previous forecasts unless the full replacement succeeds.
            with db_transaction.atomic():
                FinancialForecast.objects.all().delete()

                forecast_objects = [
                    FinancialForecast(
                        forecast_month=item["forecast_month"],
                        predicted_income=item["predicted_income"],
                        predicted_expense=item["predicted_expense"],
                        generated_at=timezone.now(),
                    )
                    for item in forecasts
                ]

                saved_forecasts = FinancialForecast.objects.bulk_create(
                    forecast_objects
                )
                create_audit_log(
                    request,
                    (
                        f"Generated {len(saved_forecasts)} financial forecast records "
                        f"for {horizon} months."
                    ),
                )
                serializer = self.get_serializer(
                    saved_forecasts,
                    many=True,
                )
                response_data = serializer.data

            return Response(
                response_data,
                status=status.HTTP_201_CREATED,
            )

        except Exception as exc:
            return Response(
                {
                    "error": "Forecast generation failed.",
                    "detail": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
# ============================================================
# AUDIT LOG VIEWSET
# ============================================================

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminOrManager]

    def get_queryset(self):
        user = self.request.user

        # Admin can see all audit logs
        if user.role.role_name == "Admin":
            return AuditLog.objects.all().order_by("-log_time")

        # Manager can see only audit logs
        # generated by users from their own branch
        if user.role.role_name == "Manager":
            return AuditLog.objects.filter(
                user__branch=user.branch
            ).exclude(
                user__role__role_name="Admin"
            ).order_by("-log_time")

        return AuditLog.objects.none()
# ============================================================
# ALERT
# ============================================================

class AlertViewSet(viewsets.ModelViewSet):
    serializer_class = AlertSerializer
    permission_classes = [IsAdminOrManagerForWriteAlerts]

    def get_queryset(self):
        user = self.request.user

        # Admin → all alerts
        if user.role.role_name == "Admin":
            return Alert.objects.all().order_by("-alert_id")

        # Manager → alerts from their branch
        if user.role.role_name == "Manager":
            return Alert.objects.filter(
                transaction__account__user__branch=user.branch
            ).order_by("-alert_id")

        # Customer → alerts related to their own transactions
        if user.role.role_name == "Customer":
            return Alert.objects.filter(
                transaction__account__user=user
            ).order_by("-alert_id")

        # Analyst → can read all alerts
        if user.role.role_name == "Analyst":
            return Alert.objects.all().order_by("-alert_id")

        # Unknown role → no alerts
        return Alert.objects.none()

    def create(self, request, *args, **kwargs):
        # Alerts are written only by transaction-screening services.
        # Do not permit fabricating predictions/alerts from the UI/API.
        raise MethodNotAllowed("POST", detail="Alerts are generated by transaction screening only.")

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed("PUT", detail="Only the review action is supported.")

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed("DELETE", detail="Original alert evidence cannot be deleted.")

    @db_transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        """Audited, atomic resolution. Original evidence is immutable."""
        allowed = {"is_resolved", "resolution_note"}
        if set(request.data) != allowed or request.data.get("is_resolved") is not True:
            raise ValidationError({
                "detail": "Supply only is_resolved=true and resolution_note."
            })
        note = request.data.get("resolution_note")
        if not isinstance(note, str) or not 10 <= len(note.strip()) <= 500:
            raise ValidationError({
                "resolution_note": "A review explanation of 10–500 characters is required."
            })

        # get_object() is scoped by get_queryset(), so managers cannot
        # resolve an alert from another branch.
        alert = self.get_object()
        current = Alert.objects.select_for_update().get(pk=alert.pk)
        if current.is_resolved:
            raise ValidationError({"detail": "This alert was already resolved."})
        current.is_resolved = True
        current.save(update_fields=["is_resolved"])
        create_audit_log(
            request,
            (
                f"Alert {current.alert_id} resolved for Transaction "
                f"{current.transaction_id}. Reason: {note.strip()}"
            ),
        )
        return Response(AlertSerializer(current).data, status=status.HTTP_200_OK)


class OperationalSnapshotView(APIView):
    """Small, permission-scoped operational snapshot for real workflow UI.

    Never return the full 50,000-row transaction table to a browser.
    Manager branch restrictions apply to every returned collection.
    """

    permission_classes = [IsAdminOrManager]

    def get(self, request):
        user = request.user
        branch_filter = (
            {} if user.role.role_name == "Admin"
            else {"user__branch": user.branch}
        )
        accounts = Account.objects.filter(**branch_filter).order_by("-account_id")
        transactions = Transaction.objects.filter(
            **(
                {} if user.role.role_name == "Admin"
                else {"account__user__branch": user.branch}
            )
        ).order_by("-transaction_id")
        alerts = Alert.objects.filter(
            **(
                {} if user.role.role_name == "Admin"
                else {"transaction__account__user__branch": user.branch}
            )
        ).order_by("-alert_id")
        audit = AuditLog.objects.filter(
            **(
                {} if user.role.role_name == "Admin"
                else {"user__branch": user.branch}
            )
        )
        if user.role.role_name == "Manager":
            # An Admin's home branch is not the same as the scope of the
            # transaction the Admin operated on; exclude Admin log actions.
            audit = audit.exclude(user__role__role_name="Admin")
        audit = audit.order_by("-log_id")
        account = request.query_params.get("account_id")
        if account:
            try:
                account_id = int(account)
            except (TypeError, ValueError):
                raise ValidationError({"account_id": "Must be an integer."})
            if not accounts.filter(account_id=account_id).exists():
                raise PermissionDenied("Account is outside your authorized scope.")
            transactions = transactions.filter(account_id=account_id)
            alerts = alerts.filter(transaction__account_id=account_id)
        recent_transactions = list(transactions[:30])
        ids = [tx.pk for tx in recent_transactions]
        predictions = FraudPrediction.objects.filter(
            transaction_id__in=ids
        ).order_by("-prediction_id")
        return Response({
            "accounts": AccountSerializer(accounts[:35], many=True).data,
            "transactions": TransactionSerializer(recent_transactions, many=True).data,
            "predictions": FraudPredictionSerializer(predictions, many=True).data,
            "alerts": AlertSerializer(alerts[:35], many=True).data,
            "audit_logs": AuditLogSerializer(audit[:35], many=True).data,
            "scope": {
                "role": user.role.role_name,
                "branch_id": user.branch_id,
                "account_filter": account,
                "max_list_items": 35,
            },
        })


# ============================================================
# JOURNAL ENTRY
# ============================================================

class JournalEntryViewSet(viewsets.ModelViewSet):

    queryset = JournalEntry.objects.all().order_by(
        "-journal_entry_id"
    )

    serializer_class = JournalEntrySerializer

    permission_classes = [IsAdminOrManager]
    http_method_names = ["get", "head", "options"]


# ============================================================
# DASHBOARD
# ============================================================

class DashboardView(APIView):
    """
    Main dashboard API.

    Provides:

    - Total transactions
    - Actual anomalies
    - Anomaly percentage
    - Total income
    - Total expense
    - Monthly income
    - Monthly expense
    - 2026 forecast
    - Fraud model performance
    - Confusion matrices
    - Forecast evaluation
    - System information
    """

    permission_classes = [IsAdminOrAnalyst]

    def get(self, request):

        try:
            data = get_dashboard_data()

            return Response(
                data,
                status=status.HTTP_200_OK,
            )

        except Exception as exc:

            return Response(
                {
                    "error": "Dashboard data could not be loaded.",
                    "detail": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ============================================================
# GEMINI MANAGEMENT REPORT
# ============================================================

class GeminiReportView(APIView):
    """
    Generate an AI management report.

    Gemini receives only verified metrics calculated by Python.

    Gemini does NOT calculate:

    - precision
    - recall
    - F1
    - confusion matrix
    - MAE
    - RMSE
    - MAPE
    - forecast values
    """

    permission_classes = [IsAdminOrAnalyst]

    def get(self, request):

        try:

            result = generate_gemini_report()

            create_audit_log(
                request,
                "Generated Gemini management financial report.",
            )


            return Response(
                result,
                status=status.HTTP_200_OK,
            )

        except ValueError as exc:

            return Response(
                {
                    "error": "Gemini configuration error.",
                    "detail": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        except Exception as exc:

            return Response(
                {
                    "error": "Unable to generate Gemini report.",
                    "detail": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ============================================================
# HEALTH CHECK
# ============================================================

class LogoutView(APIView):
    """Revoke the presented DRF token, rather than just clearing the browser."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = request.auth
        if not isinstance(token, Token):
            return Response(
                {"detail": "Token authentication is required for logout."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        token.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CurrentUserView(APIView):
    """Authenticated identity for the demo UI; never expose token or password."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "user_id": user.pk,
            "username": user.username,
            "role": user.role.role_name if user.role else None,
            "branch": user.branch.branch_name if user.branch else None,
            "can_run_demo": bool(user.role and user.role.role_name == "Admin"),
            "can_use_operations": bool(user.role and user.role.role_name in ("Admin", "Manager")),
            "can_view_global_analytics": bool(user.role and user.role.role_name in ("Admin", "Analyst")),
        })


class HealthCheckView(APIView):
    """
    Simple API health check.
    """

    permission_classes = [AllowAny]

    def get(self, request):

        return Response(
            {
                "status": "ok",
                "service": "AI Finance System",
            },
            status=status.HTTP_200_OK,
        )

