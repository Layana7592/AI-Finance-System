"""Optional real Gemini acceptance test — intentionally never run without a key.

    GEMINI_API_KEY=<set-secret-outside-Git> python manage.py verify_gemini_live \
        --output evidence/gemini_live_status.json

Produces evidence about the API response and deterministic numerical guard.
It does NOT publish key, full prompt, model raw response or unsupported claims.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
import os

from django.core.management.base import BaseCommand, CommandError

from finance.services.gemini_service import generate_gemini_report


class Command(BaseCommand):
    help = "Verify one real Gemini response with a configured API key (not mocked)"

    def add_arguments(self, parser):
        parser.add_argument("--output", required=True)

    def handle(self, *args, **options):
        if not os.getenv("GEMINI_API_KEY"):
            raise CommandError(
                "GEMINI_API_KEY is unavailable. Live Gemini verification is NOT complete."
            )
        result = generate_gemini_report()
        if result.get("report_source") != "gemini" or not result.get("gemini_available"):
            raise CommandError(
                "Gemini did not return an accepted live narrative. "
                "The fallback worked, but live verification remains incomplete."
            )
        if result.get("numeric_claims_source") != "python_only":
            raise CommandError("Unverified numerical claims in AI report.")
        if result.get("narrative_numeric_validation") != "passed":
            raise CommandError("Gemini narrative numeric validation not confirmed.")

        output = {
            "real_external_call": True,
            "status": "live_gemini_narrative_accepted",
            "recorded_utc": datetime.now(timezone.utc).isoformat(),
            "model": os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
            "numeric_claims_source": result["numeric_claims_source"],
            "narrative_numeric_validation": result["narrative_numeric_validation"],
            "source": "Gemini API called with securely supplied key; response not saved",
            "scope": "single API connectivity and policy acceptance test, not factual audit of qualitative prose",
        }
        path = Path(options["output"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(output, indent=2), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS("Real Gemini model replied and passed numeric-claim validation."))
