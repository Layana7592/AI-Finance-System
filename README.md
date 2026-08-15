# AI-Powered Finance Management and Operations System

An AI-powered finance management and operations system developed using **Django REST Framework, PostgreSQL, React, Machine Learning, and Google Gemini API**.

The system provides secure financial data management along with intelligent features such as **fraud detection, anomaly detection, financial forecasting, alerts, audit logging, and automated financial reporting**.

## Key Features

- User, Role, and Branch Management
- Account and Transaction Management
- Journal Entry Management
- AI-based Fraud Prediction
- Transaction Anomaly Detection
- Financial Forecasting
- Financial Report Management
- Alert Management
- Audit Logging
- Branch-wise Financial Analytics
- Google Gemini API Integration
- RESTful APIs using Django REST Framework

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Django + Django REST Framework |
| Frontend | React.js |
| Database | PostgreSQL |
| Machine Learning | Scikit-learn, TensorFlow, Keras |
| Anomaly Detection | Isolation Forest |
| Forecasting | LSTM / ARIMA / Prophet |
| Generative AI | Google Gemini API |
| Data Generation | Faker |
| Development | Python, Git, VS Code |

## Database Entities

The system includes:


Role
Branch
User
Account
Transaction
JournalEntry
FraudPrediction
FinancialForecast
Report
Alert
AuditLog

## Dataset

The system uses synthetic financial data generated using Django management commands and Faker.

- 50,000 transactions
- 500 anomalous transactions
- 1% anomaly rate
- Multiple branches
- Branch-wise users, accounts, and transactions

## Project Structure

AI-Finance-System/
│
├── django_backend/
│   ├── banking_system/
│   ├── finance/
│   │   ├── migrations/
│   │   ├── management/
│   │   ├── services/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
└── README.md


## Setup

git clone <repository-url>
cd AI-Finance-System/django_backend

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

python manage.py migrate
python manage.py runserver

## Synthetic Data Generation

python manage.py generate_users
python manage.py generate_accounts
python manage.py generate_transactions --count 50000

## Security

Sensitive credentials such as database passwords, Django secret keys, and Gemini API keys are stored using environment variables and are excluded from version control.

## Future Scope

- Real-time fraud detection
- Advanced AI financial analytics
- Automated report generation
- Real-time alerts
- Explainable AI
- Cloud deployment
- Advanced dashboard analytics

## Project Purpose

This project demonstrates the integration of financial management, Machine Learning, forecasting, Generative AI, and web technologies to build an intelligent and scalable finance management platform.