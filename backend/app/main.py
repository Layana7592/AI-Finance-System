from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from .database import get_db
from . import crud, schemas

app = FastAPI(title="AI Finance System")

@app.get("/")
def home():
    return {"message": "AI Finance System API"}

@app.get("/users", response_model=list[schemas.User])
def read_users(db: Session = Depends(get_db)):
    return crud.get_users(db)

@app.get("/transactions", response_model=list[schemas.Transaction])
def read_transactions(db: Session = Depends(get_db)):
    return crud.get_transactions(db)

@app.get("/transactions/{transaction_id}", response_model=schemas.Transaction)
def read_transaction(transaction_id: int, db: Session = Depends(get_db)):
    return crud.get_transaction(db, transaction_id)


@app.post("/users", response_model=schemas.User)
def create_new_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    return crud.create_user(db, user)