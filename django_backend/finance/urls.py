from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    UserViewSet,
    AccountViewSet,
    TransactionViewSet,
    FraudPredictionViewSet,
    FinancialForecastViewSet,
    AuditLogViewSet,
    AlertViewSet,
    JournalEntryViewSet,
)

router = DefaultRouter()

router.register(
    "users",
    UserViewSet
)

router.register(
    "accounts",
    AccountViewSet
)

router.register(
    "transactions",
    TransactionViewSet
)

router.register(
    "fraud-predictions",
    FraudPredictionViewSet
)

router.register(
    "forecasts",
    FinancialForecastViewSet
)

router.register(
    "audit-logs",
    AuditLogViewSet
)

router.register(
    "alerts",
    AlertViewSet
)

router.register(
    "journal-entries",
    JournalEntryViewSet
)

urlpatterns = [
    path("", include(router.urls)),
]