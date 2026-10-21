# AI Finance System

## Banking Analytics & Intelligent Financial Monitoring

AI Finance System is an academic banking analytics project built using Django REST Framework, PostgreSQL, Python, Machine Learning, statistical forecasting, React, and Google Gemini.

The system demonstrates banking data management, role-based access control, anomaly detection, financial forecasting, dashboard analytics, and AI-assisted management reporting using synthetic banking data.

> **Recovery-branch documentation (not the upstream student's repository):** This README tracks verified implementation and experiments in `Abhijith513/AI-Finance-System` at `rescue/submission-critical-fixes`. Earlier experimental outputs are retained in [Historical README Results](docs/HISTORICAL_README_RESULTS.md), and unresolved issues are tracked in [Remediation Plan](docs/REMEDIATION_MASTER_PLAN.md). Do not represent this as the unchanged upstream source or as production banking software.

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

## Current Verified Recovery Evaluation (seed 42, 17 October 2026)

The **original project's earlier experiment is preserved unchanged** in [Historical README Results](docs/HISTORICAL_README_RESULTS.md). The following results were independently recomputed on our recovery revision with 50,000 synthetic transactions and 500 artificial anomaly labels. These two sets of numbers are **different experiments/snapshots** and must not be presented as directly equivalent.

| Metric | Statistical baseline | Isolation Forest |
|---|---:|---:|
| Precision | 66.14% | 4.40% |
| Recall | 75.00% | 4.40% |
| F1 score | 70.29% | 4.40% |
| True positives | 375 | 22 |
| False positives | 192 | 478 |
| False negatives | 125 | 478 |
| True negatives | 49,308 | 49,022 |

The statistical baseline performed substantially better **on this synthetic dataset**. The anomalies are dominated by large amounts, which favours an amount-based baseline. The Isolation Forest result is **in-sample**, not a held-out generalization estimate. A chronological holdout and realistic behavioural-only anomaly experiment remain unresolved research tasks.

**Do not confuse the two fraud pipelines:** the live transaction API uses a lightweight uncalibrated behavioural risk score; Isolation Forest is an explicitly invoked offline academic benchmark. Neither is proof of real-world fraud detection accuracy.

**Source evidence:** [reproducible seed-42 metrics and 12 saved forecasts](https://github.com/Abhijith513/AI-Finance-System/actions/runs/39007808672). This artifact predates subsequent presenter improvements; refer to its commit SHA when reporting numerical results.

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

## Recovery Revision: Forecast Evaluation (seed 42)

The following figures were recomputed for the 24-month **synthetic** history. Historical README results, including the earlier 2,236.65% SARIMA expense MAPE, are preserved in [Historical README Results](docs/HISTORICAL_README_RESULTS.md); they are not current recovery results.

| Target | Model | MAPE | Validation windows |
|---|---|---:|---:|
| Income | Seasonal-Naive | 7.83% | 11 |
| Income | SARIMA | 61.62% | 10 |
| Expense | Seasonal-Naive | 3.82% | 11 |
| Expense | SARIMA | 7.97% | 10 |

**Caution:** Because SARIMA did not complete all 11 validation windows, this is **not a fully paired comparison**. The generator falls back to Seasonal-Naive on SARIMA failure or incomplete validation coverage. A matched-window comparison, residual analysis, and uncertainty intervals are planned corrective work, not completed claims.

[Download the exact metrics artifact from the verified GitHub Actions run](https://github.com/Abhijith513/AI-Finance-System/actions/runs/39007808672).

---

## Latest Demonstration Workflow (recovery branch)

- Sign in through the React login form using a **locally provisioned** `demo_presenter` Admin account.
- Click **Start timed demonstration** to create a new **synthetic** transaction and verify its fraud screen, saved alert, audit record, 12 stored forecasts and deterministic management report fallback.
- The demo is *not* a live Gemini demonstration unless a valid API key is configured and a real response is successfully checked.
- Presenter credentials are never committed; create the account using `DEMO_PRESENTER_PASSWORD` and `python manage.py prepare_demo_presenter` after bootstrapping.
- Follow [the step-by-step PGDDSA runbook](docs/PGDDSA_LIVE_DEMO_RUNBOOK.md). For live browser and frontend checks, consult [GitHub Actions](https://github.com/Abhijith513/AI-Finance-System/actions).
- Only research outputs from an exact recorded commit should be included in a formal academic report. The live demo adds synthetic transactions and therefore changes live counts.

---

## Separate chronological and behavioural research (H5–H8)

The current recovery revision includes **new, separately labelled studies** in addition to — **not instead of** — the original in-sample experiment. See [verified research findings](docs/CONTROLLED_RESEARCH_FINDINGS.md), the [prespecified protocol](docs/CONTROLLED_RESEARCH_PROTOCOL.md), and [the actual CI evidence artifact](https://github.com/Abhijith513/AI-Finance-System/actions/runs/39023138671).

- Chronological holdout of original synthetic dataset: train on the first 40,000 transactions, test on later 10,000 (115 anomalies). Isolation Forest detected **1/115**, F1 **1.72%**; statistical amount baseline detected **96/115**, F1 **91.00%**.
- Separate behaviour-only study: 6,000 synthetic events, 90 labelled anomalies entirely in the later test period. Neither Isolation Forest nor the amount-based baseline detected any; this is an openly reported **negative result**.
- **Matched-window** seasonal forecasting on exactly the same ten successful months: income Seasonal-Naive/SARIMA MAPE **7.51% / 61.57%**; expense **3.69% / 7.33%**. SARIMA failed the March 2025 window, which remains explicitly disclosed.
- Actual false-negative cases, descriptive feature contrasts, and residual/worst-window details are in the evidence JSON. No claim of causal feature attribution is made.

**Caution:** Held-out evaluation is not equivalent to the earlier in-sample results. Both datasets and fraud labels are synthetic, and a fixed 1% contamination threshold does not represent a calibrated financial-fraud probability.

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
git clone https://github.com/Abhijith513/AI-Finance-System.git
cd AI-Finance-System
git switch rescue/submission-critical-fixes
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
DJANGO_SECRET_KEY=your_django_secret_key
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
Previously verified: 58/58 Django tests on PostgreSQL and React build/lint. Latest verification is tracked through GitHub Actions; run the test workflow for the current branch head.\nEvidence: https://github.com/Abhijith513/AI-Finance-System/actions/workflows/rescue-tests.yml
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

Recovery branch: https://github.com/Abhijith513/AI-Finance-System/tree/rescue/submission-critical-fixes\n\nOriginal student repository (unchanged): https://github.com/Layana7592/AI-Finance-System\n\nAll fixes are isolated from the original repo pending explicit academic handover.\n\n---\n\n# Academic Project Note

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