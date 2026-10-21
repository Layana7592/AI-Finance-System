# Research remediation: H5–H8, controlled experiments

**Status (17 October 2026):** Experimental code and regression tests committed. *Do not publish numerical claims until the exact full-data GitHub Actions artifact has passed and been inspected.* No original experiment has been overwritten.

## Preserved benchmark

The original Isolation Forest versus amount-based statistical comparison is preserved under `docs/HISTORICAL_README_RESULTS.md`. The seed-42 50,000-row in-sample recovery benchmark is separately preserved in the `academic-submission-metrics` evidence artifact. Its Isolation Forest was fitted on the same rows used for evaluation. This is **not** a held-out result.

The original 24-month SARIMA and Seasonal-Naive figures are also kept; they used 10 SARIMA windows versus 11 baseline windows and **must not** be presented as a strict paired comparison.

## H5 — Strict chronological Isolation Forest holdout

- Sort by exact transaction timestamp and transaction ID. Fit on the first 80%; test on the last 20%, with no timestamp overlap.
- Generate the existing 24-vector account behaviour features causally: only transactions *prior to each event* are used; earlier test events may inform subsequent test features, as they would in real-time scoring. No labels or future amounts are features.
- Set contamination = 1% before seeing test labels; fix the random seed and 160 trees. This is a prespecified statistical assumption, not an empirically calibrated threshold.
- Train Isolation Forest **once on the earlier data** and never refit on the test rows. Evaluate the frozen model and the original chronological amount-based baseline on the same held-out rows.
- Report training/test dates and class prevalence, both confusion matrices, precision, recall, F1, false-alert rate, missed-anomaly rate and representative erroneous transactions.
- A low F1 here may be meaningful even if it differs from the earlier in-sample experiment. DO NOT conflate the results.

## H6 — Independent behavioural-only synthetic anomalies

Use a **separate** seeded sample of 6,000 rows across 60 synthetic accounts, with 90 labelled anomalies confined to the later testing period. Three transparent types:

1. `new_merchant_and_location`: novel merchant and location, ordinary transaction amount.
2. `night_and_type_change`: normally daytime account transacts at 02:00, unusual withdrawal and location, ordinary amount.
3. `rapid_repeat`: a transaction follows a historical account event just five seconds later, normal-sized amount.

The generator never multiplies amounts because of anomaly labels. Random sampling can still produce distribution differences; report actual median amounts. An unusual event is *not necessarily financial fraud*. The same chronological holdout protocol scores this sample independently.

## H7 — Fully matched SARIMA and baseline comparison

- Retain the complete original Seasonal-Naive evaluation (11 possible one-step windows) regardless of SARIMA fitting success.
- Record whether SARIMA completed each exact calendar month and the failure reason. Do not silently drop this information.
- Compute **new paired results** from the identical subset of months in which *both models* yielded finite predictions.
- Present matched MAE/RMSE/MAPE for income and expense, together with the matched sample size and every SARIMA failure. Clearly distinguish these from the old all-window baseline.
- An empty paired set must report unavailable (`null`) rather than a fabricated zero error. Paired comparison removes a structural bias, but successful-only windows can still be selective; disclose this limitation.
- This is one-step-ahead forecasting on 24 synthetic monthly observations; no claim of industrial forecasting reliability or model superiority outside this dataset is warranted.

## H8 — Traceable error analysis

- For both fraud experiments, report TP/FP/FN/TN, examples of false alerts and missed labelled anomalies, transaction timestamp, merchant, location, amount, known synthetic type (where generated), and the model's anomaly score.
- Report descriptive feature median contrasts between labelled cases and normal cases. These are **not** causal explanations, local SHAP values or learned importances.
- For forecasting, record each tested month with actual and predicted values; report mean signed error (bias), median absolute error, maximum absolute error and three largest-error months for matched periods, along with the failed months and reasons.
- No results should be cherry-picked to improve a preferred model.

## Reproducibility

```bash
cd django_backend
python manage.py test finance.test_research_experiments
python manage.py migrate
python manage.py bootstrap_demo_data --seed 42 --transactions 50000 --anomalies 500
python manage.py export_research_evidence --output evidence/controlled_studies.json --seed 42 --behavioural-transactions 6000 --behavioural-anomalies 90 --estimators 160
```

The exporter is read-only; it does not update `Transaction.is_anomaly`, persisted `FraudPrediction`s, forecasts, the original academic benchmark or the database.

CI: [Controlled research evidence workflow](https://github.com/Abhijith513/AI-Finance-System/actions/workflows/controlled-research.yml). Inspect and download the resulting JSON artifact. Re-run tests and regenerate evidence after any code revision that affects features, thresholds, models or timestamps.

## What remains unproven

- These are synthetic, not real financial events, with simplified habitual behaviours.
- There are no external bank fraud labels, no site-specific representativeness validation, and no blinded expert annotation.
- The behavioural generator is explicitly an invented sensitivity test to understand failure modes, not an improvement that can be claimed in the original project.
- With short historical series, full SARIMA estimation and uncertainty calibration may be unstable.
- Academic interpretation and teaching to Layana occur after the final technical revision is frozen, as requested.
