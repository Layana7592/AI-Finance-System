"""Measure real DRF request latency against a local synthetic PostgreSQL DB.

Requires an already bootstrapped test database, demo presenter and its password
provided from DEMO_PRESENTER_PASSWORD. Metrics include one cold dashboard call
and repeated warm requests; this is a single-host characterization, not an
availability, bank-scale or capacity benchmark.
"""
import json
import os
import platform
import statistics
import time
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import django
from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandError
from rest_framework.test import APIClient

from finance.models import Account, Transaction


class Command(BaseCommand):
    help = "Measure p50/p95 operational Django API latency, including warm cached dashboards"

    def add_arguments(self, parser):
        parser.add_argument("--output", required=True)
        parser.add_argument("--samples", type=int, default=8)

    def handle(self, *args, **options):
        samples = options["samples"]
        if not 5 <= samples <= 30:
            raise CommandError("Use 5–30 samples per endpoint.")
        password = os.getenv("DEMO_PRESENTER_PASSWORD")
        if not password:
            raise CommandError("Set DEMO_PRESENTER_PASSWORD without committing it.")
        if Transaction.objects.count() < 100:
            raise CommandError("Bootstrap synthetic test data before benchmarking.")
        account = Account.objects.filter(account_number="DEMO-ACCOUNT-2026").first()
        if not account:
            raise CommandError("Run prepare_demo_presenter first.")

        client = APIClient()
        auth = client.post(
            "/api/token/",
            {"username": "demo_presenter", "password": password},
            format="json",
        )
        if auth.status_code != 200 or not auth.data.get("token"):
            raise CommandError("Presenter authentication failed.")
        client.credentials(HTTP_AUTHORIZATION="Token " + auth.data["token"])

        def one(label, fn):
            t0 = time.perf_counter()
            response = fn()
            elapsed = (time.perf_counter() - t0) * 1000
            if response.status_code < 200 or response.status_code >= 300:
                raise CommandError(
                    f"{label} returned HTTP {response.status_code}."
                )
            return elapsed

        def summary(values):
            return {
                "requests": len(values),
                "min_ms": round(min(values), 2),
                "median_ms": round(statistics.median(values), 2),
                "p95_ms": round(float(np.percentile(values, 95)), 2),
                "max_ms": round(max(values), 2),
            }

        # Password authentication is independently timed from a fresh client.
        # Do not record, log or serialize the username/password or token.
        def fresh_login():
            visitor = APIClient()
            return visitor.post(
                "/api/token/",
                {"username": "demo_presenter", "password": password},
                format="json",
            )
        authentication = [
            one("fresh token login", fresh_login) for _ in range(samples)
        ]

        cache.clear()
        cold_dashboard_ms = one("cold dashboard", lambda: client.get("/api/dashboard/"))
        operations = [
            one("operations", lambda: client.get("/api/operations/"))
            for _ in range(samples)
        ]
        warm_dash = [
            one("warm dashboard", lambda: client.get("/api/dashboard/"))
            for _ in range(samples)
        ]
        fallback_reports = [
            one("management report", lambda: client.get("/api/report/"))
            for _ in range(samples)
        ]
        transaction_post = []
        for i in range(samples):
            transaction_post.append(one(
                "synthetic transaction POST",
                lambda i=i: client.post(
                    "/api/transactions/",
                    {
                        "account": account.pk,
                        "amount": "142.00",
                        "transaction_type": "Purchase",
                        "merchant": "BenchmarkMerchant",
                        "location": "Kochi",
                        "transaction_time": datetime.now(timezone.utc).isoformat(),
                        "status": "Completed",
                    },
                    format="json",
                ),
            ))
        prediction_readback = [
            one("stored fraud prediction read-back",
                lambda: client.get("/api/fraud-predictions/"))
            for _ in range(samples)
        ]
        # The repeated POSTs intentionally append synthetic transactions;
        # after this group, a dashboard request MUST reflect invalidation.
        post_write_dashboard = one(
            "post-write dashboard", lambda: client.get("/api/dashboard/")
        )

        report = {
            "captured_utc": datetime.now(timezone.utc).isoformat(),
            "source": "Synthetic dataset only; real Django/PostgreSQL APIClient",
            "environment": {
                "python": platform.python_version(),
                "django": django.get_version(),
                "system": platform.system(),
                "logical_cpus": os.cpu_count(),
                "ci_run_id": os.getenv("GITHUB_RUN_ID"),
                "commit_sha": os.getenv("GITHUB_SHA"),
            },
            "dataset_after_posts": Transaction.objects.count(),
            "sample_count_per_route": samples,
            "cold_dashboard_ms": round(cold_dashboard_ms, 2),
            "warm_dashboard": summary(warm_dash),
            "operations": summary(operations),
            "password_login": summary(authentication),
            "fraud_prediction_readback": summary(prediction_readback),
            "report_fallback_or_gemini": summary(fallback_reports),
            "new_synthetic_transaction": summary(transaction_post),
            "post_write_cache_recalculation_ms": round(post_write_dashboard, 2),
            "limitations": [
                "Sequential request measurements are not a concurrent load test.",
                "Shared GitHub runner timings are not a fixed deployment SLA.",
                "Django APIClient uses the application stack without actual network transfer.",
                "Local-memory caches are not shared among worker processes.",
                "Transaction writes append synthetic rows and invalidate evaluation cache.",
                "No live Gemini API key is used in the CI timing workflow.",
            ],
        }
        target = Path(options["output"])
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(
            f"Measured cold dashboard and {samples} sequential requests per route; output {target}"
        ))
