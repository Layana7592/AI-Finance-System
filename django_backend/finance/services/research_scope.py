"""Frozen research window for the original seed-42 synthetic experiment.

Original bootstrap_demo_data synthesizes January 2024 through December 2025.
Subsequent presenter or user transactions are operational evidence, not new
observations of that frozen academic dataset. Do not silently change benchmark
sample sizes, rolling validation months or model fits during a presentation.

This date boundary is a *versioned research-scope assumption*, NOT a general
data warehouse or real-world production transaction selection policy.
"""
from datetime import datetime, timezone

STUDY_START_UTC = datetime(2024, 1, 1, tzinfo=timezone.utc)
STUDY_END_UTC = datetime(2026, 1, 1, tzinfo=timezone.utc)
RESEARCH_SCOPE_VERSION = "synthetic-seed42-2024-2025-v1"


def research_transactions(queryset):
    """Scope studies to the stated two-year synthetic observation window."""
    return queryset.filter(
        transaction_time__gte=STUDY_START_UTC,
        transaction_time__lt=STUDY_END_UTC,
    )
