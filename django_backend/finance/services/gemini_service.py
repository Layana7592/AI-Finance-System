"""
Gemini Reporting Service

Gemini is used ONLY for reporting and interpretation.

All numerical metrics are calculated by Python first:
    - anomaly count
    - anomaly percentage
    - precision
    - recall
    - F1 score
    - confusion matrix
    - MAE
    - RMSE
    - MAPE
    - forecast values

Gemini must not calculate or invent these values.
"""

import json

from django.conf import settings
from google import genai

from .fraud_service import evaluate_fraud_models
from .forecast_service import evaluate_forecast_models


# ============================================================
# GEMINI CLIENT
# ============================================================

def get_gemini_client():
    """
    Create the Gemini client using the API key from .env.
    """

    api_key = getattr(
        settings,
        "GEMINI_API_KEY",
        None,
    )

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is not configured."
        )

    return genai.Client(
        api_key=api_key
    )


# ============================================================
# VERIFIED RESULTS
# ============================================================

def get_verified_results():
    """
    Run the application's verified evaluation functions.

    Gemini receives the results produced here.
    """

    fraud_results = evaluate_fraud_models()

    forecast_results = evaluate_forecast_models()

    return {
        "fraud_evaluation": fraud_results,
        "forecast_evaluation": forecast_results,
    }


# ============================================================
# BUILD CONTROLLED PROMPT
# ============================================================

def build_report_prompt(verified_results):
    """
    Build a controlled reporting prompt.

    Gemini is explicitly instructed not to calculate or invent
    numerical results.
    """

    results_json = json.dumps(
        verified_results,
        indent=2,
        default=str,
    )

    return f"""
You are a financial analytics reporting assistant.

Generate a concise management report using ONLY the
verified results provided below.

STRICT RULES:

1. Do not calculate any new numerical metrics.
2. Do not invent values.
3. Do not modify supplied values.
4. Do not assume missing financial information.
5. Do not create unsupported claims.
6. Use the exact values supplied by the application.
7. If information is unavailable, explicitly say it is
   unavailable.
8. Explain the results in clear business language.
9. Clearly distinguish model performance from business
   interpretation.
10. Do not claim that forecasts are guaranteed.

The report must contain:

1. Executive Summary
2. Fraud / Anomaly Detection
3. Forecasting
4. Key Findings
5. Recommendations

Fraud / Anomaly Detection should discuss:

- total transactions
- actual anomalies
- anomaly percentage
- statistical baseline precision
- statistical baseline recall
- statistical baseline F1
- statistical baseline confusion matrix
- Isolation Forest precision
- Isolation Forest recall
- Isolation Forest F1
- Isolation Forest confusion matrix
- better model according to the supplied F1 scores

Forecasting should discuss:

- total historical months
- training period
- validation period
- Seasonal-Naive performance
- SARIMA performance
- MAE
- RMSE
- MAPE
- better model based on the supplied validation metrics

The forecasting section must clearly state that the
comparison is based on chronological validation.

VERIFIED APPLICATION RESULTS:

{results_json}
"""


# ============================================================
# GENERATE REPORT
# ============================================================

def generate_gemini_report():
    """
    Generate a Gemini report from verified application results.

    Flow:

        Database
            ↓
        Python evaluation
            ↓
        Verified metrics
            ↓
        Controlled prompt
            ↓
        Gemini 3.6 Flash
            ↓
        Management report
    """

    verified_results = get_verified_results()

    prompt = build_report_prompt(
        verified_results
    )

    client = get_gemini_client()

    # Google currently recommends the Interactions API
    # for new Gemini integrations.
    interaction = client.interactions.create(
        model="gemini-3.6-flash",
        input=prompt,
    )

    report_text = getattr(
        interaction,
        "output_text",
        None,
    )

    if not report_text:
        raise RuntimeError(
            "Gemini returned an empty report."
        )

    return {
        "verified_results": verified_results,
        "report": report_text,
    }