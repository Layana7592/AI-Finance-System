# AI Finance System

## Banking Analytics & Intelligent Financial Monitoring

An AI-powered banking analytics prototype built with **Django REST Framework, PostgreSQL, Python, Machine Learning, and statistical forecasting**.

The system uses synthetic banking transaction data to demonstrate transaction monitoring, anomaly detection, financial forecasting, analytics, REST APIs, and automated testing.

> **Note:** This is an academic/research prototype using synthetic financial data.

---

## Project Status

### ✅ Implemented

- Django REST Framework backend
- PostgreSQL database integration
- Banking data models
- User, role, branch, account, and transaction management
- Journal Entry, Alert, and Audit Log models
- Synthetic banking data generation
- 50,000 synthetic transactions
- 500 labelled anomalies
- 1.00% anomaly rate
- Transaction dataset covering January 2024 – December 2025
- Statistical anomaly detection baseline
- Isolation Forest anomaly detection
- Precision, Recall, F1 Score evaluation
- Confusion matrix evaluation
- Seasonal-Naive forecasting
- SARIMA forecasting
- Chronological forecast validation
- 12-month financial forecast for 2026
- MAE, RMSE, and MAPE evaluation
- Dashboard analytics service
- Forecast APIs
- Anomaly/fraud evaluation API
- Automated Django test suite
- 17 automated tests passing
- Django migration validation
- Git and GitHub feature-branch workflow

### 🔄 In Progress

- Google Gemini AI management reporting
- AI-generated financial report integration
- Additional API improvements
- Frontend/dashboard integration refinements

### 📌 Planned

- LSTM forecasting
- Prophet forecasting
- Full regulatory automation
- Cloud deployment
- Large-scale React application
- Production authentication and authorization
- Advanced fraud detection pipeline
- Production monitoring and infrastructure

---

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Backend | Django |
| API | Django REST Framework |
| Database | PostgreSQL |
| Data Generation | Faker |
| Data Processing | Pandas |
| Machine Learning | Scikit-learn |
| Forecasting | Statsmodels |
| Forecast Models | Seasonal-Naive, SARIMA |
| Testing | Django Test Framework |
| Version Control | Git & GitHub |
| Development | VS Code |

---

## Core Features

### Banking Data Management

- User management
- Role management
- Branch management
- Account management
- Transaction management
- Journal entries
- Alerts
- Audit logs

### Anomaly Detection

The system evaluates banking transactions using:

- Statistical Baseline
- Isolation Forest

Evaluation metrics:

- Precision
- Recall
- F1 Score
- Confusion Matrix

### Financial Forecasting

The system evaluates:

- Seasonal-Naive
- SARIMA

Models are evaluated using **chronological validation** rather than random train/test splitting.

### Dashboard Analytics

The analytics layer provides:

- Total transactions
- Total income
- Total expense
- Actual anomaly count
- Anomaly percentage
- Monthly income and expense
- 2026 forecast values
- Anomaly model comparison
- Forecast evaluation metrics

---

## Dataset

The project uses **synthetic banking data** generated for development, testing, and demonstration.

| Dataset Component | Count |
|---|---:|
| Roles | 3 |
| Branches | 5 |
| Users | 500 |
| Accounts | 1,000 |
| Transactions | 50,000 |
| Anomalies | 500 |

### Anomaly Rate

```text
500 anomalies / 50,000 transactions = 1.00%


## Project Structure


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
│   │   ├── management/
│   │   │   └── commands/
│   │   │       └── bootstrap_demo_data.py
│   │   ├── services/
│   │   │   ├── fraud_service.py
│   │   │   ├── forecast_service.py
│   │   │   └── dashboard_service.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── tests.py
│   │   └── admin.py
│   │
│   ├── manage.py
│   └── requirements.txt
│
├── frontend/
├── .gitignore
└── README.md

## Current Implementation Summary


| Component                | Status         |
| ------------------------ | -------------- |
| Django Backend           | ✅ Implemented  |
| PostgreSQL               | ✅ Implemented  |
| Banking Models           | ✅ Implemented  |
| User Management          | ✅ Implemented  |
| Role Management          | ✅ Implemented  |
| Branch Management        | ✅ Implemented  |
| Account Management       | ✅ Implemented  |
| Transaction Management   | ✅ Implemented  |
| Journal Entries          | ✅ Implemented  |
| Alerts                   | ✅ Implemented  |
| Audit Logs               | ✅ Implemented  |
| Dashboard Analytics      | ✅ Implemented  |
| 50,000 Transactions      | ✅ Implemented  |
| 500 Anomaly Labels       | ✅ Implemented  |
| Statistical Baseline     | ✅ Implemented  |
| Isolation Forest         | ✅ Implemented  |
| Seasonal-Naive           | ✅ Implemented  |
| SARIMA                   | ✅ Implemented  |
| Chronological Validation | ✅ Implemented  |
| 2026 Forecast            | ✅ Implemented  |
| Forecast Evaluation      | ✅ Implemented  |
| Automated Testing        | ✅ Implemented  |
| Gemini Reporting         | 🔄 In Progress |
| Advanced AI Reporting    | 🔄 In Progress |
| LSTM                     | 📌 Planned     |
| Prophet                  | 📌 Planned     |
| Large React Application  | 📌 Planned     |
| Cloud Deployment         | 📌 Planned     |
| Regulatory Automation    | 📌 Planned     |
