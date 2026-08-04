from sqlalchemy import Column, Integer, String, ForeignKey, DECIMAL, TIMESTAMP
from .database import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    email = Column(String)
    password_hash = Column(String)
    role_id = Column(Integer)


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.account_id"))
    amount = Column(DECIMAL)
    transaction_type = Column(String)
    merchant = Column(String)
    location = Column(String)
    transaction_time = Column(TIMESTAMP)
    status = Column(String)