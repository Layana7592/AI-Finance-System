from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Numeric, TIMESTAMP, Date
from .database import Base


# ---------------- ROLES ----------------

class Role(Base):
    __tablename__ = "roles"

    role_id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String)


# ---------------- BRANCHES ----------------

class Branch(Base):
    __tablename__ = "branches"

    branch_id = Column(Integer, primary_key=True, index=True)
    branch_name = Column(String)
    city = Column(String)
    state = Column(String)
    ifsc_code = Column(String)
    phone = Column(String)


# ---------------- USERS ----------------

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    email = Column(String)
    password_hash = Column(Text)

    role_id = Column(Integer, ForeignKey("roles.role_id"))
    branch_id = Column(Integer, ForeignKey("branches.branch_id"))

    created_at = Column(TIMESTAMP)


# ---------------- ACCOUNTS ----------------

class Account(Base):
    __tablename__ = "accounts"

    account_id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.user_id"))

    account_number = Column(String)
    account_type = Column(String)
    balance = Column(Numeric)
    created_at = Column(TIMESTAMP)


# ---------------- TRANSACTIONS ----------------

class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(Integer, primary_key=True, index=True)

    account_id = Column(Integer, ForeignKey("accounts.account_id"))

    amount = Column(Numeric)
    transaction_type = Column(String)
    merchant = Column(String)
    location = Column(String)
    transaction_time = Column(TIMESTAMP)
    status = Column(String)


# ---------------- FRAUD PREDICTIONS ----------------

class FraudPrediction(Base):
    __tablename__ = "fraud_predictions"

    prediction_id = Column(Integer, primary_key=True, index=True)

    transaction_id = Column(Integer, ForeignKey("transactions.transaction_id"))

    fraud_probability = Column(Numeric)
    prediction = Column(Boolean)
    model_version = Column(String)
    predicted_at = Column(TIMESTAMP)


# ---------------- FINANCIAL FORECASTS ----------------

class FinancialForecast(Base):
    __tablename__ = "financial_forecasts"

    forecast_id = Column(Integer, primary_key=True, index=True)

    forecast_month = Column(Date)
    predicted_income = Column(Numeric)
    predicted_expense = Column(Numeric)
    generated_at = Column(TIMESTAMP)


# ---------------- AUDIT LOGS ----------------

class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.user_id"))

    action = Column(Text)
    ip_address = Column(String)
    log_time = Column(TIMESTAMP)