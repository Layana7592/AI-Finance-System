# Verified controlled research findings — issues H5–H8 (17 October 2026)

**This document describes NEW, separately labelled research experiments.** It does not replace the original historical results or the earlier seed-42 in-sample recovery benchmark. All cases and labels are artificial.

- Reproducible original-size experiment: [GitHub Actions run 39023138671](https://github.com/Abhijith513/AI-Finance-System/actions/runs/39023138671), downloadable artifact `controlled-research-evidence`, file `controlled_studies.json`.
- Source recorded in the artifact: `ed560a43c721b0f8a1d35c3bc82fbdf05fa43696` (GitHub Actions test/PR commit).
- Methods and safety limitations: [CONTROLLED_RESEARCH_PROTOCOL.md](CONTROLLED_RESEARCH_PROTOCOL.md).

## H5: Frozen-model Isolation Forest on unseen, later transactions

Chronological **training: 40,000** synthetic transactions; **testing: 10,000** later transactions. Exactly **115** labelled anomalies occur in the test period (**1.15% prevalence**). Training ended 2025-08-08 08:58:45 UTC; testing began 2025-08-08 09:21:10 UTC. Features for each transaction use earlier account history only; no test labels or future transaction features are fitted.

| Metric | Isolation Forest | Statistical amount-based baseline |
|---|---:|---:|
| Precision | 100.00% | 100.00% |
| Recall | 0.87% | 83.48% |
| F1 | **1.72%** | **91.00%** |
| True positives | 1 | 96 |
| False positives | 0 | 0 |
| False negatives | 114 | 19 |
| True negatives | 9,885 | 9,885 |

**Avoid misleading precision claims:** Isolation Forest made precisely **one** positive prediction and detected only one labelled anomaly; 100% precision is therefore not a sign of a useful detector. The amount-based baseline benefits from the original anomaly generator's amount-heavy labels. The in-sample baseline and held-out results are separate experiments and cannot be substituted for one another.

## H6: Independent behavioural-only stress test

A *different* seeded generator created **6,000 synthetic transactions** over 60 accounts. A chronological 80/20 split left 1,200 test events, of which **90 (7.5%)** were labelled anomalies: 30 novel merchant+location cases, 30 unusual-night+type cases, and 30 rapid-repeat cases. **Transaction amounts were not inflated based on anomaly labels** (normal median 878.35; labelled anomaly median 935.26 in dataset monetary units).

| Measure | Isolation Forest | Amount-based baseline |
|---|---:|---:|
| Precision | 0.00% | 0.00% |
| Recall | 0.00% | 0.00% |
| F1 | 0.00% | 0.00% |
| True positives | 0 | 0 |
| False negatives | 90 | 90 |
| True negatives | 1,110 | 1,110 |

**Negative result:** Both algorithms labelled all 1,200 test rows normal. Their apparent **92.5% accuracy** results from class imbalance. The 1% contamination setting is deliberately fixed before evaluation, while the behavioural test has 7.5% labelled exceptions; this mismatch and synthetic simplifications are relevant methodological limitations, **not proven causal diagnoses**. Descriptive behavioural feature contrasts show merchant/location novelty exists in the test features. No tuning was done to conceal this failure.

## H7: Strictly matched SARIMA and Seasonal-Naive months

The original Seasonal-Naive evaluation still retains **11 valid** one-step windows, while SARIMA produced **10 valid** windows; March 2025 raised an `IndexError`. To permit a fair numerical comparison, paired metrics use only the identical ten successful dates.

| Target | Paired sample | Seasonal-Naive MAPE | SARIMA MAPE | Model |
|---|---:|---:|---:|---|
| Income | 10 monthly windows | **7.51%** | 61.57% | Seasonal-Naive |
| Expense | 10 monthly windows | **3.69%** | 7.33% | Seasonal-Naive |

This makes the numerical comparisons matched, but conditioning on successful SARIMA windows can still introduce selection bias. The SARIMA failure is reported and NOT treated as a free pass. Only 24 synthetic monthly history points are available.

## H8: Why the models were wrong

Fraud evidence includes transaction-linked examples of true positives, false negatives and false alerts where they exist, with timestamps, synthetic amounts, merchant/location, anomaly score and known generated scenario. **All 90 behavioural cases were missed**, so there are no true-positive examples or false-alert cases to fabricate.

The descriptive (not causal) difference between anomalous and normal features in the behavioural study is high for `merchant_new`, `merchant_frequency` and `merchant_rarity`, showing a discriminating signal was present in the engineered features even though Isolation Forest did not flag it under the fixed model/threshold.

Matched SARIMA/Seasonal-Naive residuals report mean signed error, median absolute error, maximum absolute error and three worst months. Income SARIMA's worst miss was September 2025 (predicted **103.10 million** versus actual **17.35 million** synthetic monetary units). This large miss helps explain the high SARIMA mean error, but does not prove a universal model failure mechanism.

## Constraints before presenting this work

- Neither dataset establishes real banking fraud rates or deployed detector validity.
- No final university report or student-authored scientific interpretation has been claimed: the project revision must first be frozen after all 16 remediation issues.
- Original academic experiment remains separately available and unchanged.
- Raw machine-readable evidence is the authority for every rounded figure in this document.
