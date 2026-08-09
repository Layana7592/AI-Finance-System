
from django.db import models


# ============================================================
# ROLES
# ============================================================

class Role(models.Model):
    role_id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=100)

    class Meta:
        db_table = "roles"

    def __str__(self):
        return self.role_name


# ============================================================
# BRANCHES
# ============================================================

class Branch(models.Model):
    branch_id = models.AutoField(primary_key=True)
    branch_name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    ifsc_code = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)

    class Meta:
        db_table = "branches"

    def __str__(self):
        return self.branch_name


# ============================================================
# USERS
# ============================================================

class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=150)
    email = models.EmailField()
    password_hash = models.TextField()

    role = models.ForeignKey(
        Role,
        on_delete=models.DO_NOTHING,
        db_column="role_id"
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.DO_NOTHING,
        db_column="branch_id"
    )

    created_at = models.DateTimeField()

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.username


# ============================================================
# ACCOUNTS
# ============================================================

class Account(models.Model):
    account_id = models.AutoField(primary_key=True)

    user = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        db_column="user_id"
    )

    account_number = models.CharField(max_length=50)
    account_type = models.CharField(max_length=50)

    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )

    created_at = models.DateTimeField()

    class Meta:
        db_table = "accounts"

    def __str__(self):
        return self.account_number


# ============================================================
# TRANSACTIONS
# ============================================================

class Transaction(models.Model):
    transaction_id = models.AutoField(primary_key=True)

    account = models.ForeignKey(
        Account,
        on_delete=models.DO_NOTHING,
        db_column="account_id"
    )

    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )

    transaction_type = models.CharField(max_length=50)
    merchant = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    transaction_time = models.DateTimeField()
    status = models.CharField(max_length=50)

    # PostgreSQL column is SMALLINT.
    # 0 = normal
    # 1 = anomaly
    is_anomaly = models.SmallIntegerField(default=0)

    class Meta:
        db_table = "transactions"

    def __str__(self):
        return str(self.transaction_id)


# ============================================================
# FRAUD PREDICTIONS
# ============================================================

class FraudPrediction(models.Model):
    prediction_id = models.AutoField(primary_key=True)

    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.DO_NOTHING,
        db_column="transaction_id"
    )

    fraud_probability = models.DecimalField(
        max_digits=5,
        decimal_places=4
    )

    prediction = models.BooleanField()
    model_version = models.CharField(max_length=100)
    predicted_at = models.DateTimeField()

    class Meta:
        db_table = "fraud_predictions"

    def __str__(self):
        return str(self.prediction_id)


# ============================================================
# FINANCIAL FORECASTS
# ============================================================

class FinancialForecast(models.Model):
    forecast_id = models.AutoField(primary_key=True)

    forecast_month = models.DateField()

    predicted_income = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )

    predicted_expense = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )

    generated_at = models.DateTimeField()

    class Meta:
        db_table = "financial_forecasts"

    def __str__(self):
        return str(self.forecast_month)


# ============================================================
# AUDIT LOGS
# ============================================================

class AuditLog(models.Model):
    log_id = models.AutoField(primary_key=True)

    user = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        db_column="user_id"
    )

    action = models.TextField()
    ip_address = models.CharField(max_length=45)
    log_time = models.DateTimeField()

    class Meta:
        db_table = "audit_logs"

    def __str__(self):
        return str(self.log_id)


# ============================================================
# ALERTS
# ============================================================

class Alert(models.Model):
    alert_id = models.AutoField(primary_key=True)

    alert_type = models.CharField(max_length=100)
    severity = models.CharField(max_length=50)
    message = models.TextField()

    is_resolved = models.BooleanField(default=False)

    created_at = models.DateTimeField()

    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.DO_NOTHING,
        db_column="transaction_id"
    )

    class Meta:
        db_table = "alerts"

    def __str__(self):
        return str(self.alert_id)


# ============================================================
# JOURNAL ENTRIES
# ============================================================

class JournalEntry(models.Model):
    journal_entry_id = models.AutoField(primary_key=True)

    entry_date = models.DateTimeField()
    description = models.TextField()

    debit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    credit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    account = models.ForeignKey(
        Account,
        on_delete=models.DO_NOTHING,
        db_column="account_id"
    )

    class Meta:
        db_table = "journal_entries"

    def __str__(self):
        return str(self.journal_entry_id)

