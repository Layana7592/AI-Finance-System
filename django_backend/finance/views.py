from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
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
    queryset = User.objects.all().order_by("-user_id")
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


# ============================================================
# ACCOUNT
# ============================================================

class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all().order_by("-account_id")
    serializer_class = AccountSerializer
    permission_classes = [AllowAny]


# ============================================================
# TRANSACTION
# ============================================================

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all().order_by("-transaction_time")
    serializer_class = TransactionSerializer
    permission_classes = [AllowAny]


# ============================================================
# FRAUD / ANOMALY PREDICTION
# ============================================================

class FraudPredictionViewSet(viewsets.ModelViewSet):
    queryset = FraudPrediction.objects.all().order_by("-prediction_id")
    serializer_class = FraudPredictionSerializer
    permission_classes = [AllowAny]

    @action(
        detail=False,
        methods=["get"],
        url_path="evaluate",
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


# ============================================================
# FINANCIAL FORECAST
# ============================================================

class FinancialForecastViewSet(viewsets.ModelViewSet):
    queryset = FinancialForecast.objects.all().order_by(
        "forecast_month"
    )
    serializer_class = FinancialForecastSerializer
    permission_classes = [AllowAny]

    @action(
        detail=False,
        methods=["get"],
        url_path="evaluate",
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

            # ------------------------------------------------
            # IMPORTANT:
            # generate_forecast() may return FinancialForecast
            # model instances. DRF cannot return model objects
            # directly as JSON.
            # ------------------------------------------------

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

            # If the service already returns dictionaries/JSON,
            # return them directly.
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
    permission_classes = [AllowAny]


# ============================================================
# ALERT
# ============================================================

class AlertViewSet(viewsets.ModelViewSet):
    queryset = Alert.objects.all().order_by("-alert_id")
    serializer_class = AlertSerializer
    permission_classes = [AllowAny]


# ============================================================
# JOURNAL ENTRY
# ============================================================

class JournalEntryViewSet(viewsets.ModelViewSet):
    queryset = JournalEntry.objects.all().order_by(
        "-journal_entry_id"
    )
    serializer_class = JournalEntrySerializer
    permission_classes = [AllowAny]


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

    permission_classes = [AllowAny]

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

    permission_classes = [AllowAny]

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