# PGDDSA — Presenter demo guide (synthetic data)

**Purpose:** Demonstrate a real, reproducible banking-analytics workflow to examiners.
**Not:** a deployed banking system, actual fraud diagnosis, or evidence of real-world fraud-model performance.

## Launch on the presenter laptop

Prerequisites: Python 3.13, PostgreSQL, Node.js 22, npm, cloned rescue branch.

1. Use a synthetic demo database and configure django_backend/.env with DJANGO_SECRET_KEY, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT. Do not commit the .env file.
2. From django_backend:

    python -m pip install -r requirements.txt
    python manage.py migrate --noinput
    python manage.py bootstrap_demo_data --seed 42 --transactions 50000 --anomalies 500

3. Set the DEMO_PRESENTER_PASSWORD environment variable to a **private** password of at least 12 characters. Never print or commit it. Then run:

    python manage.py prepare_demo_presenter
    python manage.py runserver 127.0.0.1:8000

4. In another terminal, from frontend:

    npm ci
    npm run dev

5. Open http://127.0.0.1:5173 and log in as demo_presenter with the private password configured above. Vite proxies /api requests to Django. The token lives in browser session storage, not in hardcoded JavaScript.

The presenter command creates a synthetic administrator, a separate demo account, and twelve benign historical transactions. It does not change original research labels. Avoid rerunning bootstrap after adding the presenter; bootstrap deliberately refuses to overwrite an already modified database.

## Eight-step timed demonstration

Open Guided demo and press Start timed demonstration. Each step performs a real API request and has a measured duration.

1. Fetch live dashboard analytics.
2. Find the presenter account in PostgreSQL.
3. POST a synthetic unusual transaction (no actual money transfers).
4. Read its persisted behavioural risk prediction (not a calibrated probability).
5. Read its associated alert.
6. Read the corresponding audit log.
7. Read and verify twelve saved forecast records.
8. Request the management report. If Gemini is unavailable, the report explicitly displays fallback mode and verified Python metrics.

The walkthrough stops visibly if an expected link is absent. It displays IDs and evidence when available. Afterwards open Analytics dashboard to show actual charts, model metrics and saved forecasts, then sign out.

## Before the examiner arrives

- Test the exact laptop, database and browser twice. Time the actual run; this is not guaranteed to finish in five minutes.
- Preserve the CI screenshots and evidence JSON as backup.
- Browser CI uses a smaller 2,000-transaction synthetic dataset to validate UI workflow quickly; research evidence CI uses 50,000 transactions and 500 anomalies. Do not confuse the two.
- A successful fallback report is not a successful online Gemini call.
- Never display token values, passwords, database credentials or private information in screenshots.

## Required screenshot evidence

Login (blank password), authenticated presenter, eight backend-verified steps with elapsed time, transaction and screening score, alert and audit link, forecast row count, Gemini/fallback report, full analytics dashboard and signed-out login.

## Academic explanation

Distinguish the transaction-time BehaviouralRiskHeuristic-v1 from batch Isolation Forest. Its 0–1 score is heuristic, not an actual fraud probability. The current statistical baseline is substantially better on the synthetic benchmark. Explain why, acknowledge the data design, and separate forecast validation error from saved future forecasts.
