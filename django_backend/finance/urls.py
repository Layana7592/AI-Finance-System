
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

router.register(r"users", UserViewSet, basename="users")
router.register(r"accounts", AccountViewSet, basename="accounts")
router.register(r"transactions", TransactionViewSet, basename="transactions")
router.register(
    r"fraud-predictions",
    FraudPredictionViewSet,
    basename="fraud-predictions",
)
router.register(
    r"forecasts",
    FinancialForecastViewSet,
    basename="forecasts",
)
router.register(
    r"audit-logs",
    AuditLogViewSet,
    basename="audit-logs",
)
router.register(r"alerts", AlertViewSet, basename="alerts")
router.register(
    r"journal-entries",
    JournalEntryViewSet,
    basename="journal-entries",
)

urlpatterns = router.urls

