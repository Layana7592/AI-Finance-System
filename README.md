# AI-Powered Finance Management and Operations System

An AI-powered finance management and operations system built with **Django REST Framework and PostgreSQL**, with machine-learning-based fraud/anomaly detection and financial forecasting.

The current implementation focuses on the **Django REST API, PostgreSQL database, synthetic financial transaction generation, anomaly labelling, and financial forecasting**.

---

## Project Status

| Area | Status |
|---|---|
| Django REST Framework backend | ✅ Implemented |
| PostgreSQL database | ✅ Implemented |
| Role management | ✅ Implemented |
| Branch management | ✅ Implemented |
| Multi-branch users | ✅ Implemented |
| Account management | ✅ Implemented |
| Transaction management | ✅ Implemented |
| 50,000 synthetic transactions | ✅ Implemented |
| Transaction anomaly labelling | ✅ Implemented |
| Financial forecasting | ✅ Implemented |
| Financial Forecast API | ✅ Implemented |
| Fraud prediction API/model | 🔄 In Progress |
| Google Gemini integration | 🔄 In Progress |
| Report generation/API | 🔄 In Progress |
| React frontend | 📋 Planned |
| Isolation Forest anomaly detection | 📋 Planned |
| Advanced branch-wise analytics | 📋 Planned |

---

# Implemented

## Backend

- Django backend
- Django REST Framework
- PostgreSQL database
- RESTful API structure
- Django management commands
- Database migrations

## User and Branch Management

- Role model
- Branch model
- User model
- Users linked to roles and branches
- Multiple branches supported
- Users distributed across multiple branches

## Account Management

- Account model
- Multiple account types
- Account generation command
- Automatic `created_at` generation
- Accounts linked to users

## Transaction Management

- Transaction model
- Synthetic transaction generation using Faker
- Multiple transaction types
- Transaction status
- Transaction date and time
- Merchant and location information
- Transactions linked to accounts

## Synthetic Dataset

The project can generate:

- 50,000 financial transactions
- Data covering January 2024 to December 2025
- Multiple branches
- Multiple users
- Multiple accounts
- Approximately 1% ground-truth anomalies

The transaction generator uses seasonal factors to create variation across different months.

## Anomaly Labelling

Transactions contain a ground-truth anomaly field:

```text
0 = Normal transaction
1 = Anomalous transaction
```

Approximately 1% of generated transactions are marked as anomalies.

> **Note:** These anomaly labels are synthetic ground-truth labels generated during dataset creation. They should not be described as Isolation Forest predictions.

## Financial Forecasting

Financial forecasting is implemented using a **SARIMAX-based forecasting service**.

The system:

1. Aggregates monthly transaction data.
2. Separates income and expenses.
3. Generates future monthly forecasts.
4. Stores forecasts in the `FinancialForecast` table.
5. Exposes forecast generation through the Django REST API.

The forecast generation endpoint currently generates **12 future monthly forecasts**.

---

# In Progress

The following components exist partially or are being developed further.

## Fraud Detection

The project contains fraud prediction-related models and services.

Further work is required to complete and validate the complete machine-learning fraud detection workflow.

## Google Gemini Integration

Gemini API integration has been explored and configured during development.

However, it is not currently documented as a fully working end-to-end application feature.

Further work is required before it can be marked as fully implemented.

## Financial Reports

The database contains a `Report` model.

A complete report-generation and report-delivery workflow/API still requires further development and validation.

---

# Planned

The following features are part of the future development roadmap.

## React Frontend

A React-based frontend/dashboard is planned for:

- Financial dashboards
- Transaction monitoring
- Branch-wise analytics
- Fraud/anomaly visualization
- Forecast visualization
- Alerts
- Reports

The current repository does not contain a completed React frontend.

## Isolation Forest

Isolation Forest is planned as a machine-learning approach for unsupervised transaction anomaly detection.

The current synthetic dataset's `is_anomaly` field is a generated ground-truth label and should not be confused with Isolation Forest predictions.

## Advanced Analytics

Planned analytics include:

- Branch-wise transaction analytics
- Income and expense dashboards
- Account-level analytics
- Transaction trends
- Anomaly statistics
- Forecast visualization

## Automated Reporting

Planned functionality includes:

- Automated financial reports
- Report generation API
- Downloadable reports
- Scheduled reports

## Real-Time Alerts

Planned functionality includes:

- Real-time anomaly alerts
- Fraud alerts
- High-value transaction alerts
- Branch-level alerts

## Explainable AI

Future versions may provide explanations for:

- Fraud predictions
- Anomalous transactions
- Forecast results

---

# Technology Stack

## Current Technologies

| Component | Technology |
|---|---|
| Backend | Django |
| API | Django REST Framework |
| Database | PostgreSQL |
| Data Generation | Faker |
| Data Processing | Pandas |
| Machine Learning | Scikit-learn |
| Forecasting | Statsmodels / SARIMAX |
| Language | Python |
| Development | Git, GitHub, VS Code |

## Planned Technologies

| Component | Technology |
|---|---|
| Frontend | React.js |
| Generative AI | Google Gemini API |
| Anomaly Detection | Isolation Forest |

---

# Database Entities

The current database contains the following entities:

- Role
- Branch
- User
- Account
- Transaction
- FraudPrediction
- FinancialForecast
- Report
- Alert
- AuditLog
- JournalEntry

---

# Project Structure

```text
AI-Finance-System/
│
├── django_backend/
│   ├── banking_system/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── asgi.py
│   │   └── wsgi.py
│   │
│   ├── finance/
│   │   ├── migrations/
│   │   │
│   │   ├── management/
│   │   │   └── commands/
│   │   │       ├── generate_users.py
│   │   │       ├── generate_accounts.py
│   │   │       └── generate_transactions.py
│   │   │
│   │   ├── services/
│   │   │   ├── forecast_service.py
│   │   │   └── fraud_service.py
│   │   │
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── admin.py
│   │
│   ├── manage.py
│   └── requirements.txt
│
├── .gitignore
├── README.md
└── .env
```

> `.env` should never be committed to GitHub.

---

# Setup

## 1. Clone the Repository

```bash
git clone <repository-url>
cd AI-Finance-System/django_backend
```

## 2. Create a Virtual Environment

```bash
python -m venv venv
```

## 3. Activate the Virtual Environment

### Windows

```bash
venv\Scripts\activate
```

## 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## 5. Configure Environment Variables

Create a local `.env` file and add the required configuration such as:

```text
DJANGO_SECRET_KEY=your-secret-key
DB_NAME=your-database-name
DB_USER=your-database-user
DB_PASSWORD=your-database-password
DB_HOST=localhost
DB_PORT=5432
GEMINI_API_KEY=your-api-key
```

Do not commit `.env` to GitHub.

> A `.env.example` file is planned as part of the documentation and security improvements.

## 6. Run Migrations

```bash
python manage.py migrate
```

## 7. Check the Project

```bash
python manage.py check
```

## 8. Start the Development Server

```bash
python manage.py runserver
```

---

# Synthetic Data Generation

The commands should be executed in the following order.

## 1. Generate Users

```bash
python manage.py generate_users --count 100
```

The command creates required roles and branches if they do not already exist and generates users across available branches.

Users are distributed across the available branches instead of assigning every user to the first branch.

## 2. Generate Accounts

```bash
python manage.py generate_accounts --count 100
```

Accounts are generated for existing users.

The account generation command automatically sets the required `created_at` field.

## 3. Generate Transactions

```bash
python manage.py generate_transactions --count 50000
```

This generates 50,000 synthetic financial transactions covering January 2024 to December 2025.

The transaction generator includes:

- Multiple transaction types
- Transaction statuses
- Merchant information
- Location information
- Seasonal transaction variation
- Synthetic anomaly labels

---

# Forecast Generation

The financial forecasting service uses historical transaction data to generate future monthly income and expense forecasts.

The forecasting process:

1. Retrieves transaction data from PostgreSQL.
2. Aggregates transactions by month.
3. Separates income and expense transactions.
4. Uses SARIMAX for time-series forecasting.
5. Generates future monthly predictions.
6. Stores the results in the `FinancialForecast` table.

The forecast generation service generates **12 future monthly forecasts** by default.

---

# API

The backend uses **Django REST Framework**.

The financial forecasting functionality includes a forecast-generation action.

Example:

```text
POST /api/forecast/generate/
```

The exact API routes depend on the configured Django REST Framework router.

---

# Current Dataset Verification

The current development database has been verified with:

```text
Users        : 611
Accounts     : 784
Transactions : 50,000
Branches     : 6
```

The transaction dataset covers:

```text
January 2024 → December 2025
```

The current database contains users distributed across multiple branches.

Example branch distribution:

```text
Kannur Branch      -> 135 users
Kochi Branch       -> 116 users
Kozhikode Branch   -> 113 users
Trivandrum Branch  -> 121 users
Bangalore Branch   -> 108 users
Calicut Branch     -> 18 users
```

---

# Security

Sensitive configuration values such as:

- Django secret key
- PostgreSQL credentials
- API keys

should be stored in environment variables and must not be committed to GitHub.

A local `.env` file should be used for development configuration.

A `.env.example` file is planned for future documentation and setup improvements.

---

# Future Scope

Future development may include:

- React frontend
- Isolation Forest anomaly detection
- Complete Gemini integration
- Advanced fraud detection
- Automated report generation
- Report API
- Real-time alerts
- Branch-wise dashboards
- Explainable AI
- Cloud deployment

---

# Project Purpose

This project demonstrates the development of a financial management backend using **Django REST Framework and PostgreSQL**, together with synthetic financial data generation, anomaly labelling, fraud-detection components, and machine-learning-based financial forecasting.

The project is being developed incrementally, with **Implemented, In Progress, and Planned** features clearly separated.