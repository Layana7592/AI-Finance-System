# Submission stabilization — October 2026

## Scope
This branch prioritizes a defensible demonstration and safe persistence, not a
production banking implementation. Do not merge into Layana's original without
reviewing test results.

## Fraud workflow
- `POST /api/transactions/` runs an *account-bounded*, chronological,
  explainable behavioural screening rule using at most 250 prior transactions
  plus the new transaction. It does not train Isolation Forest.
- `FraudPrediction.model_version = BehaviouralRiskHeuristic-v1` identifies
  these live scores. The legacy database field `fraud_probability` holds an
  **uncalibrated risk score (0–1)**, NOT an empirical fraud probability.
  The 0.60 alert threshold is a demo heuristic; it has not been calibrated or
  validated as real-world fraud detection.
- Transaction creation, screening, any alert, and audit logging happen in
  one database transaction (all commit or all roll back).
- The transaction API intentionally disallows PATCH, PUT and DELETE after
  creation. Corrections need a separate reversal/amendment workflow in future;
  this avoids silently invalidating previously generated predictions and alerts.
- Isolation Forest remains an offline academic benchmark.
  Run `python manage.py generate_fraud_predictions` explicitly when you want
  to persist batch predictions. Model evaluation compares the existing
  benchmark methods with synthetic labels; do not mix its metrics with the
  live heuristic.

## Forecast workflow
- The same calendar months are used for income and expense series.
- Expanding-window validation always retains Seasonal-Naive observations even
  where SARIMA fails. The two methods expose their respective observation
  counts; incomplete SARIMA coverage disqualifies SARIMA from selection.
- Invalid and unavailable metrics are `null` in API JSON, not an invented zero.
- Forecast generation uses the validation MAPE when available, a guarded SARIMA
  fit and a Seasonal-Naive fallback for fitting failures/nonfinite outputs.
- `POST /api/forecasts/generate/` accepts horizons 1–24. Replacement and
  auditing are atomic; failure retains the earlier forecast records.
- Any historical README metrics predate these changes. Recompute all metrics
  and replace report figures only after a verified run.

## Verification commands
From `django_backend` after configuring PostgreSQL and migrations:
```bash
python manage.py test finance.test_rescue finance.test_workflow_stability
python manage.py test
python manage.py bootstrap_demo_data
python manage.py generate_fraud_predictions
```
Then log in as an authorized Admin for POST workflow checks, and demonstrate
that manager/customer permissions and write restrictions are enforced.

## Reporting limitations
This is synthetic-data anomaly *screening*, not verified fraud detection.
The synthetic anomalies are predominantly exaggerated amounts. Isolation
Forest is evaluated in-sample, so generalization is unknown. SARIMA performance
on short histories may be unstable. Submit these limitations honestly.
