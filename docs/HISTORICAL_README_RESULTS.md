# Original README research results — archived verbatim

**Provenance:** Original `main` repository benchmark narrative, inherited at fork time, before the recovery-branch changes. These numbers are historical and MUST NOT be substituted for the verified seed-42 recovery-run results. They are preserved for traceability and to avoid concealing the original experiment. The original project's exact experimental configuration and environment may differ; equivalence has not been established.

## Original fraud results

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



## Original forecast results

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


