"""Transparent horizon-specific empirical intervals for Seasonal-Naive forecasts.

With 24 months of monthly data, only a few horizons have enough historical
errors for calibration. Longer horizons return unavailable, never guessed bands.
These are exploratory split-free prequential conformal-style intervals whose
nominal coverage depends on exchangeability of historical errors, which is
UNVERIFIED in the original synthetic data. Report empirical coverage cautiously.
"""
from math import ceil
import numpy as np

from .forecast_service import get_monthly_transaction_data, seasonal_naive_forecast


def _rolling_errors(series, horizon, min_train=13):
    rows = []
    for origin in range(min_train, len(series) - horizon + 1):
        train = series.iloc[:origin]
        prediction = float(seasonal_naive_forecast(train, horizon)[horizon - 1])
        observed = float(series.iloc[origin + horizon - 1])
        if np.isfinite(prediction) and np.isfinite(observed):
            rows.append({
                "target_month": series.index[origin + horizon - 1].date().isoformat(),
                "predicted": round(prediction, 2),
                "actual": round(observed, 2),
                "absolute_error": abs(prediction - observed),
            })
    return rows


def horizon_uncertainty(series, maximum_horizon=12, confidence=0.80,
                        min_calibration=8):
    if not 0.5 <= confidence <= 0.95:
        raise ValueError("confidence outside supported empirical interval range")
    if not 1 <= maximum_horizon <= 24:
        raise ValueError("horizon must be 1–24")
    if min_calibration < 8:
        raise ValueError("At least 8 prior residuals are required.")

    results = []
    for h in range(1, maximum_horizon + 1):
        residual_rows = _rolling_errors(series, h)
        n = len(residual_rows)
        result = {
            "horizon_months": h,
            "calibration_samples": n,
            "confidence_nominal": confidence,
            "method": "Seasonal-Naive horizon-specific rolling absolute-error order statistic",
            "lower": None,
            "upper": None,
            "point_forecast": None,
            "status": "insufficient_calibration",
        }
        if len(series) >= 13:
            predicted = float(seasonal_naive_forecast(series, h)[h-1])
            if np.isfinite(predicted):
                result["point_forecast"] = round(max(0.0, predicted), 2)
        if n >= min_calibration and result["point_forecast"] is not None:
            order = ceil((n+1)*confidence)
            # If the finite-sample rank exceeds n there is no finite
            # conformal bound at the requested level.
            if order <= n:
                radius = float(sorted(x["absolute_error"] for x in residual_rows)[order-1])
                point = result["point_forecast"]
                result.update({
                    "lower": round(max(0.0, point-radius), 2),
                    "upper": round(point+radius, 2),
                    "calibration_radius": round(radius, 2),
                    "status": "illustrative_empirical_interval",
                })

        # A tiny prequential coverage diagnostic can be inspected,
        # but is never claimed as an independently validated rate.
        checks = []
        for j in range(min_calibration, len(residual_rows)):
            prior = sorted(x["absolute_error"] for x in residual_rows[:j])
            rank = ceil((j+1)*confidence)
            if rank <= len(prior):
                checks.append(residual_rows[j]["absolute_error"] <= prior[rank-1])
        result["prequential_coverage_checks"] = len(checks)
        result["prequential_covered"] = int(sum(checks))
        results.append(result)
    return results


def evaluate_uncertainty(maximum_horizon=12, confidence=0.80):
    series = get_monthly_transaction_data()
    out = {}
    for label in ("income", "expense"):
        data = series[label]
        out[label] = {
            "history_months": len(data),
            "horizons": horizon_uncertainty(data, maximum_horizon, confidence),
        }
    return {
        "data": out,
        "nominal_coverage": confidence,
        "scope": "synthetic monthly series; Seasonal-Naive baseline only",
        "restrictions": [
            "Historical absolute errors need not be exchangeable across years.",
            "Only a small number of rolling windows exist in 24 historical months.",
            "Reported intervals are exploratory, not validated conditional coverage.",
            "SARIMA forecasts are NOT assigned Seasonal-Naive uncertainty bands.",
            "Unavailable horizons are shown as unavailable, never extrapolated.",
            "No actual bank deposits or risk reduction can be inferred.",
        ],
    }
