from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .ledger_api import SyntheticLedgerView
from .uncertainty_api import ForecastUncertaintyView

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
    CurrentUserView,
    LogoutView,
    OperationalSnapshotView,
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
    path("me/", CurrentUserView.as_view(), name="current-user"),
    path("operations/", OperationalSnapshotView.as_view(), name="operational-snapshot"),
    path("synthetic-ledger/", SyntheticLedgerView.as_view(), name="synthetic-ledger"),
    path("forecast-uncertainty/", ForecastUncertaintyView.as_view(), name="forecast-uncertainty"),
    path("logout/", LogoutView.as_view(), name="logout"),
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