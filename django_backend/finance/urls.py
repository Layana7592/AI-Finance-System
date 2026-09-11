from django.urls import include, path
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
    DashboardView,
    GeminiReportView,
)

router = DefaultRouter()

router.register("users", UserViewSet)
router.register("accounts", AccountViewSet, basename="account")
router.register("transactions", TransactionViewSet, basename="transaction")
router.register("fraud-predictions", FraudPredictionViewSet)
router.register("forecasts", FinancialForecastViewSet)
router.register("audit-logs", AuditLogViewSet)
router.register("alerts", AlertViewSet, basename="alert")
router.register("journal-entries", JournalEntryViewSet)

urlpatterns = [
    path("", include(router.urls)),

    path(
        "dashboard/",
        DashboardView.as_view(),
        name="dashboard",
    ),

    path(
        "report/",
        GeminiReportView.as_view(),
        name="gemini-report",
    ),
]