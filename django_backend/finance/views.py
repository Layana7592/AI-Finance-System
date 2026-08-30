from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .services.dashboard_service import get_dashboard_data

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

from .services.forecast_service import generate_forecast
from .services.dashboard_service import get_dashboard_data


# ==================================================
# USER API
# ==================================================

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


# ==================================================
# ACCOUNT API
# ==================================================

class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]


# ==================================================
# TRANSACTION API
# ==================================================

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]


# ==================================================
# FRAUD PREDICTION API
# ==================================================

class FraudPredictionViewSet(viewsets.ModelViewSet):
    queryset = FraudPrediction.objects.all()
    serializer_class = FraudPredictionSerializer
    permission_classes = [IsAuthenticated]


# ==================================================
# FINANCIAL FORECAST API
# ==================================================

class FinancialForecastViewSet(viewsets.ModelViewSet):
    queryset = FinancialForecast.objects.all().order_by(
        "forecast_month"
    )

    serializer_class = FinancialForecastSerializer
    permission_classes = [IsAuthenticated]

    @action(
        detail=False,
        methods=["post"],
        url_path="generate"
    )
    def generate(self, request):

        try:
            results = generate_forecast(12)

            serializer = FinancialForecastSerializer(
                results,
                many=True
            )

            return Response(
                {
                    "message": "Forecast generated successfully",
                    "forecasts": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:

            return Response(
                {
                    "error": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ==================================================
# AUDIT LOG API
# ==================================================

class AuditLogViewSet(viewsets.ModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]


# ==================================================
# ALERT API
# ==================================================

class AlertViewSet(viewsets.ModelViewSet):
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]


# ==================================================
# JOURNAL ENTRY API
# ==================================================

class JournalEntryViewSet(viewsets.ModelViewSet):
    queryset = JournalEntry.objects.all()
    serializer_class = JournalEntrySerializer
    permission_classes = [IsAuthenticated]


# ==================================================
# DASHBOARD API
# ==================================================

class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):

        try:
            data = get_dashboard_data()

            return Response(
                data,
                status=status.HTTP_200_OK,
            )

        except Exception as e:

            return Response(
                {
                    "error": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

# ==================================================
# DASHBOARD API
# ==================================================

from rest_framework.views import APIView


class DashboardView(APIView):
    permission_classes = []

    def get(self, request):
        try:
            data = get_dashboard_data()

            return Response(
                data,
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {
                    "error": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ==================================================
# GEMINI MANAGEMENT REPORT API
# ==================================================

from rest_framework.views import APIView
from .services.gemini_service import generate_gemini_report


class GeminiReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            result = generate_gemini_report()

            return Response(
                {
                    "status": "success",
                    "report": result["report"],
                    "verified_results": result["verified_results"],
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {
                    "status": "error",
                    "error": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )