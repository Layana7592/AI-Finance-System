from sqlalchemy.orm import Session
from . import models

def get_users(db: Session):
    return db.query(models.User).all()


def get_transactions(db: Session):
    return db.query(models.Transaction).all()


def get_transaction(db: Session, transaction_id: int):
    return (
        db.query(models.Transaction)
        .filter(models.Transaction.transaction_id == transaction_id)
        .first()
    )


def create_user(db: Session, user):
    new_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=user.password_hash,
        role_id=user.role_id
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user