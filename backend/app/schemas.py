from pydantic import BaseModel

class User(BaseModel):
    user_id: int
    username: str
    email: str

    class Config:
        from_attributes = True


class Transaction(BaseModel):
    transaction_id: int
    amount: float
    transaction_type: str
    merchant: str
    location: str
    status: str

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str
    email: str
    password_hash: str
    role_id: int