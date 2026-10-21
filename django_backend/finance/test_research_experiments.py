"""Academic experiment integrity regression tests — no network or DB required."""
from copy import deepcopy
from unittest.mock import patch

import numpy as np
import pandas as pd
from django.test import SimpleTestCase

from finance.services.forecast_service import (
    expanding_window_validation, evaluate_forecast_models,
)
from finance.services.fraud_service import _build_chronological_features
from finance.services.research_experiments import (
    ANOMALY_TYPES,
    evaluate_behavioural_study,
    evaluate_chronological_holdout,
    generate_behavioural_study,
)


class BehaviouralGeneratorTests(SimpleTestCase):
    def test_generator_is_seeded_normal_amounts_and_labelled_test_only(self):
        a = generate_behavioural_study(seed=19, accounts=10, transactions=500, anomalies=24)
        b = generate_behavioural_study(seed=19, accounts=10, transactions=500, anomalies=24)
        self.assertEqual(
            [(x.transaction_id, str(x.amount), x.is_anomaly, x.anomaly_kind, x.transaction_time) for x in a],
            [(x.transaction_id, str(x.amount), x.is_anomaly, x.anomaly_kind, x.transaction_time) for x in b],
        )
        self.assertEqual(len(a), 500)
        self.assertEqual(sum(x.is_anomaly for x in a), 24)
        self.assertEqual(
            set(x.anomaly_kind for x in a if x.is_anomaly), set(ANOMALY_TYPES)
        )
        # Labels have no effect on generated monetary values or a fit-time
        # feature. The anomaly is behaviour (place, merchant, hour, velocity).
        self.assertLess(
            max(float(x.amount) for x in a if x.is_anomaly), 9500.01
        )
        self.assertTrue(all(x.transaction_time >= a[400].transaction_time
                            for x in a if x.is_anomaly))

    def test_feature_construction_uses_no_future_rows_or_label_column(self):
        rows = generate_behavioural_study(seed=42, accounts=8, transactions=400, anomalies=10)
        prefix = rows[:200]
        original, _ = _build_chronological_features(prefix)
        all_features, _ = _build_chronological_features(rows)
        self.assertTrue(np.allclose(original, all_features[:200]))

        unlabeled = deepcopy(prefix)
        for row in unlabeled:
            row.is_anomaly = 1 - row.is_anomaly
        unlabeled_features, _ = _build_chronological_features(unlabeled)
        self.assertTrue(np.allclose(original, unlabeled_features))


class ChronologicalHoldoutTests(SimpleTestCase):
    def test_holdout_is_strictly_later_and_metrics_conserve_rows(self):
        rows = generate_behavioural_study(seed=42, accounts=12, transactions=600, anomalies=24)
        result = evaluate_chronological_holdout(rows, seed=42, estimators=12)
        self.assertEqual(result["train_rows"] + result["test_rows"], 600)
        self.assertLess(result["training_end"], result["test_start"])
        self.assertGreater(result["test_anomalies"], 0)
        cm = result["isolation_forest"]["confusion_matrix"]
        self.assertEqual(sum(map(sum, cm)), result["test_rows"])
        self.assertEqual(
            result["confusion_counts"]["fn"] + result["confusion_counts"]["tp"],
            result["test_anomalies"],
        )
        self.assertEqual(result["estimators"], 12)
        for category, examples in result["cases"].items():
            self.assertLessEqual(len(examples), 8)

    def test_train_only_fitting_never_supplies_test_labels(self):
        rows = generate_behavioural_study(seed=18, accounts=10, transactions=500, anomalies=20)
        class RecordingForest:
            fit_rows = None
            def __init__(self, *args, **kwargs):
                pass
            def fit(self, matrix):
                RecordingForest.fit_rows = len(matrix)
            def decision_function(self, matrix):
                return np.zeros(len(matrix))
            def predict(self, matrix):
                return np.ones(len(matrix))
        with patch("finance.services.research_experiments.IsolationForest", RecordingForest):
            report = evaluate_chronological_holdout(rows, estimators=10)
        self.assertEqual(RecordingForest.fit_rows, report["train_rows"])
        self.assertEqual(report["test_rows"], 100)

    def test_behavioural_report_preserves_a_separate_scenario(self):
        report = evaluate_behavioural_study(
            seed=42, accounts=10, transactions=500, anomalies=20, estimators=10
        )
        self.assertEqual(report["test_anomalies"], 20)
        self.assertEqual(sum(report["anomaly_type_counts"].values()), 20)
        self.assertIn("behaviour", report["scenario"].lower())
        self.assertIn("false_negative", report["cases"])

    def test_invalid_time_boundary_rejected(self):
        rows = generate_behavioural_study(seed=17, accounts=10, transactions=500, anomalies=20)
        for row in rows:
            row.transaction_time = rows[0].transaction_time
        with self.assertRaisesRegex(ValueError, "overlap"):
            evaluate_chronological_holdout(rows, estimators=10)


class PairedForecastTests(SimpleTestCase):
    def setUp(self):
        self.series = pd.Series(
            np.arange(1, 25, dtype=float) * 13,
            index=pd.date_range("2024-01-01", periods=24, freq="MS"),
        )

    def test_paired_metrics_only_use_successful_same_months(self):
        series = self.series.copy()
        # The window that SARIMA fails has an unusual baseline error,
        # making the paired-vs-unpaired comparison observably different.
        series.iloc[13] = 9999.0

        def deliberately_fail_first(train, horizon):
            if len(train) == 13:
                raise ValueError("controlled SARIMA failure")
            return np.repeat(train.iloc[-1], horizon)

        with patch(
            "finance.services.forecast_service.sarima_forecast",
            side_effect=deliberately_fail_first,
        ):
            result = expanding_window_validation(series, initial_train_size=13)
        self.assertEqual(result["observations"], 11)
        self.assertEqual(result["sarima_observations"], 10)
        self.assertEqual(result["paired"]["observations"], 10)
        self.assertEqual(len(result["sarima_failures"]), 1)
        self.assertEqual(result["sarima_failures"][0]["month"], "2025-02-01")
        successful = [w for w in result["validation_windows"] if w["sarima_status"] == "success"]
        failed = [w for w in result["validation_windows"] if w["sarima_status"] == "failed"]
        self.assertEqual(len(successful), 10)
        self.assertEqual(len(failed), 1)
        self.assertTrue(all(w["seasonal_naive"] is not None and w["sarima"] is not None for w in successful))
        self.assertIsNone(failed[0]["sarima"])
        paired_naive = result["paired"]["seasonal_naive"]
        self.assertIsNotNone(paired_naive["mae"])
        self.assertNotEqual(paired_naive["mae"], result["seasonal_naive"]["mae"])
        self.assertEqual(
            result["paired"]["sarima"]["mae"], result["sarima"]["mae"]
        )
        self.assertEqual(
            result["paired"]["baseline_error_analysis"]["observations"], 10
        )

    def test_all_sarima_failures_return_null_paired_metrics_not_zero(self):
        with patch(
            "finance.services.forecast_service.sarima_forecast",
            side_effect=RuntimeError("model failed"),
        ):
            result = expanding_window_validation(self.series, initial_train_size=13)
        self.assertEqual(result["paired"]["observations"], 0)
        self.assertIsNone(result["paired"]["seasonal_naive"]["mae"])
        self.assertEqual(len(result["sarima_failures"]), 11)
        self.assertEqual(result["observations"], 11)

    def test_full_forecast_evaluation_includes_paired_observations_and_residuals(self):
        with patch(
            "finance.services.forecast_service.get_monthly_transaction_data",
            return_value={"income": self.series, "expense": self.series},
        ), patch(
            "finance.services.forecast_service.check_stationarity",
            return_value={"stationary": False},
        ), patch(
            "finance.services.forecast_service.sarima_forecast",
            side_effect=ValueError("can't fit"),
        ):
            evaluation = evaluate_forecast_models()
        for key in ("income", "expense"):
            validation = evaluation[key]["validation"]
            self.assertEqual(validation["observations"], 11)
            self.assertEqual(validation["paired_comparison"]["observations"], 0)
            self.assertEqual(len(validation["windows"]), 11)
