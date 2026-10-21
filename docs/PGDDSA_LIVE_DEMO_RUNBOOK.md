# PGDDSA final demonstration — reproducible runbook

**Purpose:** demonstrate a real, traced Django/PostgreSQL/React workflow to an examiner. This is synthetic research data, not operational banking software.

## Preconditions — one time

1. Checkout the verified branch `rescue/submission-critical-fixes` of `Abhijith513/AI-Finance-System`; do not use the unrepaired upstream `main`.
2. Configure PostgreSQL and the variables `DJANGO_SECRET_KEY`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT` in `django_backend/.env` (untracked).
3. Install `django_backend/requirements.txt` in a Python environment and run:
   ```bash
   cd django_backend
   python manage.py migrate
   python manage.py bootstrap_demo_data --seed 42 --transactions 50000 --anomalies 500
   ```
   Bootstrap seeds 50,000 **synthetic** transactions and 12 saved forecasts. Use a clean database for the initial bootstrap.
4. Set `DEMO_PRESENTER_PASSWORD` as an environment variable to an original password of at least 12 characters. **Do not write a working password in GitHub, command history, screenshots, logs, or documentation.** Run `python manage.py prepare_demo_presenter`. This idempotently creates the role-protected `demo_presenter` user, synthetic account `DEMO-ACCOUNT-2026`, and 12 ordinary account-history transactions.
5. Start `python manage.py runserver 127.0.0.1:8000`.
6. In a separate terminal, run `cd frontend && npm ci && npm run dev -- --host 127.0.0.1 --port 5173`. The Vite proxy forwards `/api` requests to the real Django backend. For nonlocal deployment, set `VITE_API_BASE_URL` and configure trusted hosts/CORS deliberately.
7. Open `http://127.0.0.1:5173`, sign in as `demo_presenter` using the locally set password, and select the **Guided demo** tab.

## Timed live walkthrough

- Start with the login screen. Confirm the role and signed-in identity are displayed.
- Click **Start timed demonstration**. The UI measures actual request times. There is **no fabricated or promised fixed duration**.
- Observe eight direct API-backed checks:
  1. Dashboard metrics and chart input from backend
  2. Presenter account found in PostgreSQL
  3. New, extreme **synthetic** transaction created
  4. Behavioural heuristic prediction persisted and flagged
  5. Alert persisted for that transaction
  6. Audit entry persisted for the same transaction
  7. Twelve saved monthly forecasts retrieved
  8. Management report generated from verified Python metrics; **Gemini fallback is an acceptable, explicitly labelled result** when no key is provided
- The demo stops and shows the exact failure if any required record or response is missing. Use the **Analytics dashboard** tab to show charts; return to **Guided demo** for the transaction evidence and management report.
- Sign out. The frontend POSTs to `/api/logout/`, which **revokes the actual Django authentication token on the server** before clearing sessionStorage. If revocation fails, the UI shows an error rather than falsely claiming a successful logout. Never expose or read out the token.

## Important methodological statements

- The live heuristic is not the academic Isolation Forest benchmark. Its stored `fraud_probability` field is actually an **uncalibrated risk score**.
- The synthetic dataset's ground-truth anomalies are not real-world fraud. The benchmark model's published performance is in-sample.
- A newly created demo transaction may change current dashboard and report totals; differentiate **current live API results** from the seed-42 benchmark evaluation artifact used in the written report.
- Historical data and future forecasts should not be represented as guaranteed predictions or ledger-balanced bank balances.
- A repeat click creates a NEW synthetic transaction, alert and audit record. Avoid repeating in front of the examiner without explaining that database writes are persistent.

## Automated proof

- The browser GitHub Actions workflow `.github/workflows/presenter-demo.yml` starts a fresh PostgreSQL database, bootstraps synthetic history, prepares a presenter, starts the real Django API and Vite, uses headless Chromium to sign in and run the steps, and (only if successful) captures a time-stamped workflow log and real screenshots.
- Browser run: https://github.com/Abhijith513/AI-Finance-System/actions/workflows/presenter-demo.yml
- Full Django + frontend regression tests: https://github.com/Abhijith513/AI-Finance-System/actions/workflows/rescue-tests.yml
- Academic benchmark evidence: https://github.com/Abhijith513/AI-Finance-System/actions/workflows/report-evidence.yml

**Do not claim browser acceptance before the browser workflow finishes green and screenshots are inspected.**
