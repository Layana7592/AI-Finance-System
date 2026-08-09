
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

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


# ==================================================
# USER API
# ==================================================

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


# ==================================================
# ACCOUNT API
# ==================================================

class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer


# ==================================================
# TRANSACTION API
# ==================================================

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer


# ==================================================
# FRAUD PREDICTION API
# ==================================================

class FraudPredictionViewSet(viewsets.ModelViewSet):
    queryset = FraudPrediction.objects.all()
    serializer_class = FraudPredictionSerializer


# ==================================================
# FINANCIAL FORECAST API
# ==================================================

class FinancialForecastViewSet(viewsets.ModelViewSet):
    queryset = FinancialForecast.objects.all()
    serializer_class = FinancialForecastSerializer

    @action(
        detail=False,
        methods=["post"],
        url_path="generate"
    )
    def generate(self, request):
        try:
            results = generate_forecast()

            return Response(
                {
                    "message": "Forecast generated successfully",
                    "forecasts": results,
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


# ==================================================
# ALERT API
# ==================================================

class AlertViewSet(viewsets.ModelViewSet):
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer


# ==================================================
# JOURNAL ENTRY API
# ==================================================

class JournalEntryViewSet(viewsets.ModelViewSet):
    queryset = JournalEntry.objects.all()
    serializer_class = JournalEntrySerializer

