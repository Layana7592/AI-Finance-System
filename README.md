# AI Finance System

## Banking Analytics & Intelligent Financial Monitoring

AI Finance System is an academic banking analytics project built using Django REST Framework, PostgreSQL, Python, Machine Learning, statistical forecasting, React, and Google Gemini.

The system demonstrates banking data management, role-based access control, anomaly detection, financial forecasting, dashboard analytics, and AI-assisted management reporting using synthetic banking data.

> **Note:** This is an academic/research prototype using synthetic data. It is not intended for real-world banking deployment.

---

# 1. Project Status

The following components are currently implemented:

- Django backend
- Django REST Framework APIs
- PostgreSQL database
- Banking data models
- Role-based authentication and permissions
- Branch-level access control
- Synthetic banking dataset
- 50,000 transactions
- 500 synthetic anomaly labels
- Statistical anomaly baseline
- Isolation Forest anomaly detection
- Seasonal-Naive forecasting
- SARIMA forecasting
- Chronological forecast validation
- React dashboard
- Google Gemini management reporting
- Automated backend testing

---

# 2. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend and data processing |
| Django | Backend framework |
| Django REST Framework | REST APIs |
| PostgreSQL | Database |
| Faker | Synthetic banking data |
| Pandas | Data processing |
| NumPy | Numerical computation |
| Scikit-learn | Machine learning |
| Statsmodels | Statistical forecasting |
| Isolation Forest | Anomaly detection |
| SARIMA | Financial forecasting |
| React | Frontend dashboard |
| Vite | Frontend development/build |
| Recharts | Dashboard charts |
| Google Gemini | AI management reporting |

---

# 3. System Architecture

```text
                    React Dashboard
                           |
                           v
                 Django REST Framework
                           |
          +----------------+----------------+
          |                |                |
          v                v                v
    Authentication    Banking APIs     Analytics APIs
          |                |                |
          v                v                v
    Role & Access       PostgreSQL      ML / Forecasting
                                           |
                         +-----------------+----------------+
                         |                 |                |
                         v                 v                v
                  Anomaly Detection   Forecasting      Gemini Report
                         |                 |                |
                         +-----------------+----------------+
                                           |
                                           v
                                  Dashboard Analytics
```

---

# 4. Core Features

## 4.1 Banking Data Management

The system provides management and API support for:

- Users
- Roles
- Branches
- Accounts
- Transactions
- Journal Entries
- Alerts
- Audit Logs

The system supports multiple banking branches and branch-aware access for authorized users.

---

# 5. Authentication and Role-Based Access Control

The backend uses Django REST Framework authentication and permission classes.

## Supported Roles

- Admin
- Manager
- Analyst
- Customer

## General Access Model

| Role | Access |
|---|---|
| Admin | Full administrative access |
| Manager | Branch-level management access |
| Analyst | Analytics, anomaly detection and forecasting |
| Customer | Own account and transaction access |

Unauthenticated users cannot access protected APIs.

Customers are restricted to their own account and transaction data.

Managers are restricted according to branch-level access rules.

Analysts can access analytics, anomaly detection and forecasting features.

---

# 6. Synthetic Banking Dataset

The project uses synthetic banking data generated using Python and Faker.

| Dataset Component | Count |
|---|---:|
| Roles | 4 |
| Branches | 5 |
| Users | 500+ |
| Accounts | 1,000 |
| Transactions | 50,000 |
| Labelled Anomalies | 500 |

## Transaction Period

```text
January 2024 - December 2025
```

## Anomaly Rate

```text
500 / 50,000 = 1.00%
```

The anomaly labels are synthetic ground-truth labels created for model evaluation.

---

# 7. Anomaly / Fraud Detection

The system evaluates transactions using two approaches.

## 7.1 Statistical Baseline

A statistical/rule-based baseline is used as a reference model.

## 7.2 Isolation Forest

Isolation Forest is used as an unsupervised machine-learning anomaly detection method.

The system compares both approaches using:

- Precision
- Recall
- F1 Score
- Accuracy
- Confusion Matrix

## Current Evaluation

### Dataset

```text
Transactions: 50,000
Actual anomalies: 500
Anomaly rate: 1.00%
```

## Statistical Baseline

```text
Precision: 0.0971
Recall:    0.0400
F1 Score:  0.0567
Accuracy:  0.9867
```

### Confusion Matrix

```text
[[49314, 186],
 [480,    20]]
```

## Isolation Forest

```text
Precision: 0.0720
Recall:    0.0720
F1 Score:  0.0720
Accuracy:  0.9814
```

### Confusion Matrix

```text
[[49036, 464],
 [464,    36]]
```

These results are based on the synthetic evaluation dataset and should not be interpreted as real-world banking fraud performance.

---

# 8. Financial Forecasting

The system forecasts monthly financial activity using:

- Seasonal-Naive
- SARIMA

The forecasting pipeline uses chronological validation rather than random train/test splitting.

## Historical Data

```text
24 months
January 2024 - December 2025
```

## Forecast Horizon

```text
12 months
January 2026 - December 2026
```

## SARIMA Configuration

```text
Order: (1, 1, 1)
Seasonal Order: (1, 1, 1, 12)
Seasonality: 12 months
```

---

# 9. Forecast Validation

The system uses:

```text
Expanding-window one-step-ahead validation
```

Forecast performance is measured using:

- MAE
- RMSE
- MAPE

Stationarity is also checked using the Augmented Dickey-Fuller test.

## Income Forecast Evaluation

| Model | MAE | RMSE | MAPE |
|---|---:|---:|---:|
| Seasonal-Naive | 1,679,409.90 | 1,838,216.28 | 10.30% |
| SARIMA | 1,850,466.74 | 2,585,678.28 | 10.29% |

## Expense Forecast Evaluation

| Model | MAE | RMSE | MAPE |
|---|---:|---:|---:|
| Seasonal-Naive | 3,492,657.63 | 3,847,290.43 | 7.03% |
| SARIMA | 1,084,914,455.67 | 3,211,907,274.48 | 2,236.65% |

The evaluation results are displayed in the dashboard so that the performance of the two forecasting approaches can be compared.

---

# 10. Dashboard Analytics

The React dashboard displays backend-generated analytics including:

- Total transactions
- Total income
- Total expense
- Actual anomaly count
- Anomaly percentage
- Monthly transaction trends
- Income trends
- Expense trends
- 2026 forecast values
- Fraud/anomaly model metrics
- Confusion matrices
- Forecast evaluation
- Stationarity information
- System information
- Gemini management report

The frontend retrieves data from the Django REST API rather than using hard-coded dashboard values.

---

# 11. Google Gemini AI Reporting

Google Gemini is integrated as a management-reporting layer.

The application first calculates verified numerical results using Python.

Gemini then receives those verified results and generates a natural-language management report.

## Gemini Responsibilities

Gemini is used for:

- Interpreting anomaly detection results
- Interpreting forecasting results
- Summarizing model performance
- Explaining important findings
- Providing management-level recommendations
- Presenting limitations and warnings

## Important Design Principle

Python is responsible for the numerical calculations.

Gemini is responsible for interpreting the verified results.

This prevents the AI reporting layer from becoming the source of the application's core numerical calculations.

If Gemini becomes unavailable, the application can still retain the verified analytics results rather than depending entirely on the AI service.

---

# 12. REST API

Main API resources include:

```text
/api/users/
/api/accounts/
/api/transactions/
/api/fraud-predictions/
/api/forecasts/
/api/audit-logs/
/api/alerts/
/api/journal-entries/
/api/dashboard/
/api/report/
```

## Authentication Endpoint

```text
/api/token/
```

The APIs use Django REST Framework authentication and permission classes.

---

# 13. Project Structure

```text
AI-Finance-System/
│
├── django_backend/
│   │
│   ├── banking_system/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── asgi.py
│   │   └── wsgi.py
│   │
│   ├── finance/
│   │   ├── migrations/
│   │   ├── management/
│   │   │   └── commands/
│   │   │
│   │   ├── services/
│   │   │   ├── fraud_service.py
│   │   │   ├── forecast_service.py
│   │   │   ├── dashboard_service.py
│   │   │   └── gemini_service.py
│   │   │
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── permissions.py
│   │   ├── tests.py
│   │   ├── urls.py
│   │   └── views.py
│   │
│   ├── manage.py
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── main.jsx
│   │   └── ...
│   │
│   ├── public/
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.js
│   └── ...
│
├── .gitignore
└── README.md
```

> `.env` contains sensitive configuration such as API keys and should never be committed to GitHub.

---

# 14. Backend Setup

## Clone Repository

```powershell
git clone https://github.com/Layana7592/AI-Finance-System.git
cd AI-Finance-System
```

## Create Virtual Environment

### Windows PowerShell

```powershell
cd django_backend
python -m venv venv
.\venv\Scripts\Activate.ps1
```

## Install Dependencies

```powershell
pip install -r requirements.txt
```

---

# 15. Environment Configuration

Create a `.env` file inside:

```text
django_backend/.env
```

## Example

```env
SECRET_KEY=your_django_secret_key
DEBUG=True

DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=5432

GEMINI_API_KEY=your_gemini_api_key
```

Never commit the real `.env` file to GitHub.

The `.gitignore` file is configured to exclude sensitive environment files.

---

# 16. Database Setup

Make sure PostgreSQL is running.

Apply Django migrations:

```powershell
python manage.py migrate
```

---

# 17. Generate Demo Data

The project includes management commands for generating demonstration data.

The demonstration dataset is designed around:

```text
50,000 transactions
500 anomalies
```

---

# 18. Run Backend

From:

```text
AI-Finance-System/django_backend
```

run:

```powershell
python manage.py runserver
```

## Backend

```text
http://127.0.0.1:8000/
```

## API

```text
http://127.0.0.1:8000/api/
```

---

# 19. Frontend Setup

Open another terminal:

```powershell
cd E:\AI-Finance-System\frontend
```

## Install Dependencies

```powershell
npm install
```

## Run the React Development Server

```powershell
npm run dev
```

The Vite development server will display the frontend URL in the terminal.

---

# 20. Build Frontend

For a production build:

```powershell
npm run build
```

The build output is generated in:

```text
frontend/dist/
```

---

# 21. Testing

Run the Django automated test suite:

```powershell
cd E:\AI-Finance-System\django_backend
.\venv\Scripts\Activate.ps1
python manage.py test
```

## Current Verified Result

```text
39 tests
39 passed
0 failed
```

---

# 22. Security

The project includes:

- Token-based authentication
- Backend permission enforcement
- Role-based access control
- Branch-level access restrictions
- Protected API endpoints
- Environment-based secret configuration
- `.env` exclusion from Git
- API keys kept outside source code

This project is an academic prototype and has not been hardened for deployment in a real banking environment.

---

# 23. Limitations

This project uses synthetic banking data.

Therefore:

- Anomaly labels are synthetic.
- Model performance does not represent real banking fraud detection performance.
- Forecasts are estimates based on historical synthetic data.
- Gemini is an interpretation layer and not the source of verified numerical calculations.
- The system is not intended to replace real banking fraud, compliance, risk, or regulatory systems.

---

# 24. Future Enhancements

Possible future improvements include:

- LSTM forecasting
- Prophet forecasting
- More advanced anomaly detection
- Real-time transaction monitoring
- Advanced branch-wise analytics
- Regulatory rule automation
- Cloud deployment
- Production monitoring
- Containerization
- Scalable background processing
- Expanded React modules
- More comprehensive audit and security controls

---

# 25. Current Implementation Summary

| Component | Status |
|---|---|
| Django Backend | Implemented |
| Django REST Framework | Implemented |
| PostgreSQL | Implemented |
| Banking Models | Implemented |
| User Management | Implemented |
| Role Management | Implemented |
| Branch Management | Implemented |
| Account Management | Implemented |
| Transaction Management | Implemented |
| Journal Entries | Implemented |
| Alerts | Implemented |
| Audit Logs | Implemented |
| Token Authentication | Implemented |
| Role-Based Permissions | Implemented |
| Branch-Level Access | Implemented |
| Dashboard Analytics | Implemented |
| 50,000 Transactions | Implemented |
| 500 Anomaly Labels | Implemented |
| Statistical Baseline | Implemented |
| Isolation Forest | Implemented |
| Seasonal-Naive | Implemented |
| SARIMA | Implemented |
| Chronological Validation | Implemented |
| 2026 Forecast | Implemented |
| Forecast Evaluation | Implemented |
| React Dashboard | Implemented |
| Gemini Reporting | Implemented |
| Automated Testing | Implemented |
| LSTM | Planned |
| Prophet | Planned |
| Cloud Deployment | Planned |
| Advanced Regulatory Automation | Planned |

---

# 26. GitHub Repository

https://github.com/Layana7592/AI-Finance-System

---

# Academic Project Note

This project demonstrates the integration of:

```text
Banking Data
     ↓
PostgreSQL
     ↓
Django REST Framework
     ↓
Authentication & Role-Based Access
     ↓
Anomaly Detection
     ↓
Financial Forecasting
     ↓
Dashboard Analytics
     ↓
Gemini AI Management Reporting
```

The project is intended for academic demonstration, learning, and research using synthetic financial data.