"""One small Gemini free-tier API request; never print/export secrets."""
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

model = "gemini-3.8-flash"
secret = os.getenv("GEMINI_API_KEY", "")
output = Path(os.getenv("GEMINI_PROBE_OUTPUT", "evidence/gemini_free_tier_check.json"))
output.parent.mkdir(parents=True, exist_ok=True)
result = {
    "checked_utc": datetime.now(timezone.utc).isoformat(),
    "model": model,
    "credential_present": bool(secret),
    "raw_credential_or_response_saved": False,
    "status": "not_run",
    "limitation": "One short connectivity test, not a full financial report validation.",
}
success = False
if not secret:
    result["status"] = "missing_github_secret"
    print("GEMINI_CHECK: MISSING_SECRET")
else:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": "Return exactly one word: VERIFIED"}]}],
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": 120,
            "thinkingConfig": {"thinkingLevel": "low"},
        },
    }
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": secret},
        method="POST",
    )
    try:
        with urlopen(request, timeout=35) as response:
            body = json.load(response)
        answer = " ".join(
            str(part.get("text", ""))
            for candidate in body.get("candidates", [])
            for part in candidate.get("content", {}).get("parts", [])
        ).strip()
        result["http_status"] = 200
        result["status"] = ("accepted_and_answered" if "VERIFIED" in answer.upper()
                            else "api_accepted_but_unexpected_output")
        usage = body.get("usageMetadata") or {}
        result["usage_tokens"] = {
            field: usage[field]
            for field in ("promptTokenCount", "candidatesTokenCount", "totalTokenCount")
            if isinstance(usage.get(field), int)
        }
        success = result["status"] == "accepted_and_answered"
        print("GEMINI_CHECK: " + result["status"].upper())
    except HTTPError as exc:
        code = int(exc.code)
        result["http_status"] = code
        result["status"] = {
            400: "invalid_request_or_model_access",
            401: "invalid_credential",
            403: "permission_or_project_restricted",
            404: "model_not_available_to_key",
            429: "free_tier_quota_or_rate_limit",
        }.get(code, "http_error")
        print(f"GEMINI_CHECK: {result['status'].upper()} HTTP {code}")
    except URLError:
        result["status"] = "network_unavailable"
        print("GEMINI_CHECK: NETWORK_UNAVAILABLE")
    except (TimeoutError, ValueError, OSError):
        result["status"] = "timeout_or_invalid_response"
        print("GEMINI_CHECK: TIMEOUT_OR_INVALID_RESPONSE")

output.write_text(json.dumps(result, indent=2), encoding="utf-8")
raise SystemExit(0 if success else 1)
