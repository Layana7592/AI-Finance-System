from rest_framework import status, viewsets
from rest_framework.response import Response
from .serializers import UserSerializer, UserCreateSerializer
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from .permissions import IsAdminOrManager, IsAdminManagerOrAnalyst
from .permissions import IsAdminOrManagerForWrite
from .permissions import IsAdminOrManagerForWriteAlerts
from rest_framework.views import APIView

from .models import (
    User,
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
# USER
# ============================================================

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrManager]

    def get_queryset(self):
        user = self.request.user

        if user.role.role_name == "Admin":
            return User.objects.all().order_by("-user_id")

        if user.role.role_name == "Manager":
            return User.objects.filter(
                branch=user.branch
            ).order_by("-user_id")

        return User.objects.none()


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

# ============================================================
# TRANSACTION
# ============================================================

class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAdminOrManagerForWrite]

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


# ============================================================
# FRAUD / ANOMALY PREDICTION
# ============================================================

class FraudPredictionViewSet(viewsets.ModelViewSet):
    queryset = FraudPrediction.objects.all().order_by("-prediction_id")
    serializer_class = FraudPredictionSerializer
    permission_classes = [IsAdminManagerOrAnalyst]

    @action(
        detail=False,
        methods=["get"],
        url_path="evaluate",
        permission_classes = [IsAdminManagerOrAnalyst],
    )
    def evaluate(self, request):
        """
        Evaluate Statistical Baseline and Isolation Forest.
        Metrics are calculated by Python.
        """
        try:
            results = evaluate_fraud_models()

            return Response(
                results,
                status=status.HTTP_200_OK,
            )

        except Exception as exc:
            return Response(
                {
                    "error": "Fraud model evaluation failed.",
                    "detail": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
## ============================================================
# FINANCIAL FORECAST
# ============================================================

class FinancialForecastViewSet(viewsets.ModelViewSet):
    queryset = FinancialForecast.objects.all().order_by(
        "forecast_month"
    )
    serializer_class = FinancialForecastSerializer
    permission_classes = [IsAdminManagerOrAnalyst]

    @action(
        detail=False,
        methods=["get"],
        url_path="evaluate",
        permission_classes=[IsAdminManagerOrAnalyst],
    )
    def evaluate(self, request):
        """
        Compare Seasonal-Naive and SARIMA using
        chronological validation.
        """
        try:
            results = evaluate_forecast_models()

            return Response(
                results,
                status=status.HTTP_200_OK,
            )

        except Exception as exc:
            return Response(
                {
                    "error": "Forecast model evaluation failed.",
                    "detail": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(
        detail=False,
        methods=["post"],
        url_path="generate",
        permission_classes=[IsAdminOrManager],
    )
    def generate(self, request):
        """
        Generate future financial forecasts.
        The forecast service may return Django model objects.
        These are serialized before being returned by the API.
        """

        horizon = request.data.get("horizon", 12)

        try:
            horizon = int(horizon)

            if horizon <= 0:
                return Response(
                    {
                        "error": "Horizon must be greater than zero."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except (TypeError, ValueError):
            return Response(
                {
                    "error": "Horizon must be an integer."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from .services.forecast_service import generate_forecast

            forecasts = generate_forecast(horizon)

            if isinstance(forecasts, FinancialForecast):
                serializer = self.get_serializer(forecasts)

                return Response(
                    serializer.data,
                    status=status.HTTP_200_OK,
                )

            if isinstance(forecasts, (list, tuple)):
                serializer = self.get_serializer(
                    forecasts,
                    many=True,
                )

                return Response(
                    serializer.data,
                    status=status.HTTP_200_OK,
                )

            return Response(
                forecasts,
                status=status.HTTP_200_OK,
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
# AUDIT LOG
# ============================================================

class AuditLogViewSet(viewsets.ModelViewSet):

    queryset = AuditLog.objects.all().order_by("-log_id")
    serializer_class = AuditLogSerializer

    permission_classes = [IsAdminOrManager]
    http_method_names = ["get", "head", "options"]

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

    permission_classes = [IsAdminManagerOrAnalyst]

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

    permission_classes = [IsAdminManagerOrAnalyst]

    def get(self, request):

        try:

            result = generate_gemini_report()

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