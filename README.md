#  AI-Powered Finance Management and Operations System

An AI-powered finance management system developed using **FastAPI**, **PostgreSQL**, and **SQLAlchemy**. This project aims to build a secure backend for managing financial data and serves as a foundation for AI-powered features such as fraud detection, anomaly detection, and financial forecasting.

---

#  Project Overview

The AI-Powered Finance Management and Operations System is a backend application designed to securely manage financial information through RESTful APIs. The system uses PostgreSQL for data storage and FastAPI for API development. It follows a modular architecture, making it scalable for future AI and analytics modules.

This repository currently contains the backend implementation, database schema, and synthetic financial transaction dataset.

---

#  Current Features

- PostgreSQL database integration
- FastAPI REST API
- SQLAlchemy ORM
- Environment variable configuration using `.env`
- CRUD operations for Users (Create and Read)
- Financial Transactions API
- Swagger API Documentation
- Modular backend architecture
- 50,000 synthetic financial transactions stored in PostgreSQL

---

#  Technology Stack

### Backend
- Python
- FastAPI
- SQLAlchemy
- Uvicorn

### Database
- PostgreSQL

### Libraries
- Faker
- psycopg2-binary
- python-dotenv
- Pydantic

### API Testing
- Swagger UI

---

# 📂 Project Structure

```
AI-Finance-System/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── crud.py
│   │
│   ├── generate_transactions.py
│   ├── requirements.txt
│   ├── .env
│   └── venv/
│
├── frontend/
│
├── README.md
└── .gitignore
```

---

#  Database

The PostgreSQL database currently includes the following tables:

- Roles
- Users
- Accounts
- Transactions
- Audit Logs
- Predictions
- Notifications

---

#  Synthetic Dataset

To simulate real-world financial activity, the project includes:

- **50,000 synthetic financial transactions**

Each transaction contains:

- Account ID
- Transaction Type
- Amount
- Merchant Name
- Location
- Transaction Time
- Status

The dataset was generated using the **Faker** Python library and stored in PostgreSQL.

---

# 🔌 Available REST APIs

### Home

```
GET /
```

Response

```json
{
    "message": "AI Finance System API"
}
```

---

### Users

#### Get All Users

```
GET /users
```

Returns all registered users.

---

#### Create User

```
POST /users
```

Example Request

```json
{
    "username": "layana",
    "email": "layana@gmail.com",
    "password_hash": "123456",
    "role_id": 3
}
```

---

### Transactions

#### Get All Transactions

```
GET /transactions
```

Returns all financial transactions.

---

#### Get Transaction by ID

```
GET /transactions/{transaction_id}
```

Returns a specific transaction.

---

#  Installation

## Clone the Repository

```bash
git clone https://github.com/Layana7592/AI-Finance-System.git
```

---

## Create Virtual Environment

```bash
python -m venv venv
```

Activate

Windows

```bash
venv\Scripts\activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configure Environment Variables

Create a `.env` file inside the backend directory.

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fintech_db
DB_USER=postgres
DB_PASSWORD=your_password
```

---

## Run the Application

```bash
uvicorn app.main:app --reload
```

---

## API Documentation

Swagger UI

```
http://127.0.0.1:8000/docs
```

---

#  Current Progress

✅ PostgreSQL configured

✅ Database schema created

✅ Users inserted

✅ Accounts inserted

✅ Generated and imported 50,000 synthetic financial transactions

✅ FastAPI connected with PostgreSQL

✅ REST APIs implemented

- GET /users
- GET /transactions
- GET /transactions/{transaction_id}
- POST /users

---

#  Upcoming Features

- Update User API (PUT)
- Delete User API (DELETE)
- Role-Based Access Control (RBAC)
- JWT Authentication
- Audit Logging
- AI-based Fraud Detection
- Transaction Anomaly Detection
- Financial Forecasting
- Dashboard Analytics
- Report Generation
- Frontend Development

---

