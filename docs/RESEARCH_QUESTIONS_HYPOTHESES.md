# Research questions, hypotheses and decision rules
**AI Finance System — PGDDSA / Kannur University. Working research design, 17 October 2026.**

## Academic integrity statement
The questions below were written **after inspecting the original synthetic benchmark results**. They are **retrospective/exploratory research hypotheses**, not preregistered confirmatory hypotheses. A single seed and synthetic generator cannot establish statistical generalization, causal explanations, or validity for real financial fraud. The original experiment remains separately documented. Do not claim hypothesis confirmation merely because two observed percentages differ.

## RQ1 — Does training Isolation Forest without test-period information improve or diminish detection credibility?

**H0 (descriptive operational null):** Isolation Forest does not exceed the amount-based statistical baseline in held-out F1 at the prespecified contamination setting.

**H1:** Isolation Forest has strictly higher held-out F1 than the amount-based statistical baseline.

**Design:** Time-ordered 80/20 split on the original seeded 50,000 synthetic transactions. Fit Isolation Forest only on earlier observations; compute history-based features using information known before each event. Evaluate both detectors on identical later rows, with a fixed 1% Isolation Forest contamination assumption.

**Measures:** Confusion matrix, precision, recall, F1, test anomaly prevalence, false alerts per 100 transactions and missed anomaly rate. Report actual training and test date boundaries. Reject binary model-superiority claims if the test labels are synthetic and the difference has not been replicated across distinct periods/seeds.

**Observed exploratory result:** Isolation Forest identified 1 of 115 labelled held-out anomalies; statistical baseline found 96 of 115. This rejects the *descriptive direction* H1 on this synthetic test, but does not constitute a population-level significance test or evidence of actual bank fraud detection.

## RQ2 — Does removing obvious amount inflation reveal weaknesses in anomaly screening?

**H0 (descriptive):** Both detectors have zero true-positive detections on behavioural-only anomalies under their existing fixed settings.

**H1:** At least one detector identifies a nonzero proportion of labelled behavioural anomalies without explicit amount inflation.

**Design:** Independently seeded 6,000 events, 60 synthetic accounts, 90 labelled test-period behavioural deviations. The anomaly types are merchant-and-location novelty, nighttime/type change, and rapid account activity; amounts use the *same generating distribution* for all labels. Keep the original amount-heavy experiment unchanged.

**Measures:** Type counts, normal versus exception amount medians, detection and false-positive rates, precision/recall/F1 and examples of false negatives. The behavioural generator is a sensitivity probe, not a bank-realism validation.

**Observed exploratory result:** Both detectors detected 0 of 90 labelled test anomalies. On this constructed test, H0's observed direction holds. This shows limitations of these particular detectors/settings, not that all anomaly detection fails.

## RQ3 — Does SARIMA outperform Seasonal-Naive on strictly paired one-step forecasts?

**H0:** SARIMA's matched-window MAPE is not lower than Seasonal-Naive's matched-window MAPE.

**H1:** SARIMA's matched-window MAPE is lower than Seasonal-Naive's on the same successful calendar months.

**Design:** Retain all available expanding-window Seasonal-Naive predictions from the original 24-month synthetic history. Record SARIMA fitting failures. Construct an explicitly new *paired* evaluation using only the same months for which both models return finite predictions; retain failed months in the evidence.

**Measures:** Matched-month MAE, RMSE, MAPE, window count, signed residual bias, worst absolute error and failed-month reasons. Report original 11-window baseline separately. No statistical claim from a 10-month small and selectively successful sample.

**Observed exploratory result:** Paired income MAPE: Seasonal-Naive 7.51% versus SARIMA 61.57%; paired expense MAPE 3.69% versus SARIMA 7.33%. One SARIMA window failed in March 2025. H1's directional claim is not supported on this synthetic sample.

## RQ4 — Can software operations be demonstrated independently of the models' research accuracy?

**H0:** A complete authenticated transaction lifecycle cannot be demonstrated with committed storage and audit evidence.

**H1:** On a fresh synthetic PostgreSQL installation, a permitted user can create a transaction, retrieve its stored screening output, inspect an alert, record a justified review decision, and read the corresponding audit trail.

**Design:** Real Django + PostgreSQL + Chromium; Admin and branch Manager roles, with forbidden cross-branch actions. The test fails on missing stored records, incomplete audit trails, or unauthorized access.

**Measures:** Browser completion, HTTP status, read-after-write correctness, atomicity, permission denial, side effects, timing and screenshot evidence. A role-based UI is evidence of a research prototype, not bank-grade security certification.

**Status:** The original guided eight-step workflow and login/logout previously passed. An expanded operator investigation workflow is now under testing; do not count RQ4's new resolution step until its browser and permissions tests pass.

## Evaluation matrix

| RQ | Dataset | Principal metric | Bias or validity threat | Demonstration artifact |
|---|---|---|---|---|
| RQ1 | Original synthetic, chronological split | Held-out F1, recall, confusion counts | Artificial anomaly labels; fixed 1% contamination | Original-data held-out JSON |
| RQ2 | Independent behaviour-only synthetic | Recall by anomaly type and missed events | Engineered synthetic habits may be unrealistic | Behavioural-only JSON |
| RQ3 | 24-month aggregate synthetic series | Paired MAPE and residuals; fit failure counts | Short series; successful-window selection | Matched-month forecast JSON |
| RQ4 | Fresh local synthetic database | Persisted workflow correctness and authorization | One-machine demonstration; no external bank | Browser screenshots, API logs, CI |

## Reporting and reproducibility discipline

- The original model and dataset experiments are retained and cited separately; do not overwrite unfavourable metrics.
- Source-backed sample sizes, seed, code SHA, metric definitions, exact dates, failure windows and limitations must accompany every result.
- These are exploratory demonstrations, not p-value-based confirmatory tests; no inferential conclusion is made without independent replication.
- Numerical results must come from the exported JSON and application code, never be supplied by an LLM report.
- Any claim that one detector is universally better, real fraud was found, or SARIMA is intrinsically inferior would exceed the evidence.
- Final report wording and student teaching will follow the technical freeze, after the entire remediation plan and repository comparison are complete.

**Source protocol:** [Controlled Research Protocol](CONTROLLED_RESEARCH_PROTOCOL.md); [GitHub controlled research CI run](https://github.com/Abhijith513/AI-Finance-System/actions/runs/39023138671).
