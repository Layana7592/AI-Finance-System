from django.contrib import admin

from .models import (
    Role,
    Branch,
    User,
    Account,
    Transaction,
    FraudPrediction,
    FinancialForecast,
    Report,
    AuditLog,
    Alert,
    JournalEntry,
)


admin.site.register(Role)
admin.site.register(Branch)
admin.site.register(User)
admin.site.register(Account)
admin.site.register(Transaction)
admin.site.register(FraudPrediction)
admin.site.register(FinancialForecast)
admin.site.register(Report)
admin.site.register(AuditLog)
admin.site.register(Alert)
admin.site.register(JournalEntry)
