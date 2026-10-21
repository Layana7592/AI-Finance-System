# Issues 9–12 — Operational and research acceptance log

**Repository:** `Abhijith513/AI-Finance-System` at `rescue/submission-critical-fixes`. Layana's original repository and the fork's `main` remain unchanged. **Do not merge or hand over before the agreed full technical freeze.**

**Status:** Code and independent regression tests implemented; latest full PostgreSQL and Chromium runs are **pending**. An earlier benchmark attempt failed because a new test fixture omitted distinct email addresses; test fixtures have been corrected. Status must be updated from actual green CI runs only.

## Issue 9 — Usable operational interface and accountable review

**Implemented:** `frontend/src/OperationalWorkspace.jsx` exposes an authenticated operational view for Admin/Manager: choose an authorized account, create one synthetic transaction, verify stored risk-score read-back, review a bounded alert queue, record a 10–500 character resolution reason, verify the updated alert state and view the audit record. No application-bank ledger balance is implied.

**Server policy:** `GET /api/operations/` returns bounded and role-scoped transaction/account/prediction/alert/audit data. Manager only sees own-branch accounts, transactions and alerts. Audit views exclude Admin-originated cross-branch actions that a Manager might otherwise see via the Admin's home branch. Alert creation is reserved for screening. Normal API PUT/DELETE are rejected; PATCH requires `is_resolved=true` and `resolution_note`. Resolution and audit write are atomic; repeated resolutions are rejected, with the original alert message unchanged.

**Acceptance tests:** `finance.test_operations_performance_reporting` checks manager scope, forbidden cross-branch access, honest alert creation guards, resolution reason, audit persistence and repeated-review rejection. `frontend/scripts/presenter-e2e.mjs` additionally creates and resolves a synthetic alert through Chromium. **Await current-head green CI.**

## Issue 10 — Dashboard model-fit latency

**Implemented:** `finance.services.cached_research` caches *only* research-model evaluations: Isolation Forest benchmark and SARIMA/Seasonal-Naive validation. Live summary figures and forecasts remain separately queried. Keys are derived from a cheap DB transaction fingerprint (row count, IDs, amount sum, anomaly sum and time boundaries), database identity and a schema version; the default bounded TTL is 900 seconds. Changes to amounts/totals and appended synthetic transactions alter the fingerprint. Other manual in-place edits that preserve this fingerprint may stay cached until TTL expiry. Shared cache for multiple workers would require an external backend such as Redis; Django's default local cache is per worker.

**Acceptance:** repeated identical reads must avoid refitting ML; append must invalidate. Test with mock fit counters in `finance.test_operations_performance_reporting`. Run `.github/workflows/operational-benchmarks.yml` to record actual cold dashboard, warm dashboard, operational reads, report reads and transaction POST p50/p95 on 50k synthetic records. The benchmark is sequential Django APIClient workload on a GitHub runner, **not** a concurrent production deployment/SLA. **Await green timing artifact.**

## Issue 11 — Gemini model integration and numerical safety

**Implemented:** Python renders numeric report claims from the real computation. The optional Gemini model (`gemini-3.8-flash`, configurable by `GEMINI_MODEL`) can add only a nonnumeric qualitative interpretation. The validator rejects digits, spelled-out quantities and forbidden certification/guarantee claims. Invalid, empty or unavailable external responses lead to a labelled Python-only fallback. The response includes numeric provenance and narrative validation status.

**Evidence distinction:** unit tests simulate accepted/rejected API responses to verify the protective code. **A real external Gemini API call has NOT been verified.** The missing requirement is a valid `GEMINI_API_KEY` supplied privately in the runtime's untracked environment (never chat, commit, GitHub logs or screenshot) and an actual success from:

```bash
cd django_backend
python manage.py verify_gemini_live --output evidence/gemini_live_status.json
```

This command fails if no key is configured, the service falls back, or numeric validation fails. It writes a sanitized pass/fail record without dumping the key or raw model output. Even one successful response demonstrates connection and numeric filtering, **not** the factual accuracy of all model opinions or deployment readiness. Keep the gate open until a real run is observed.

## Issue 12 — Experimental questions and hypotheses

**Implemented:** `docs/RESEARCH_QUESTIONS_HYPOTHESES.md` defines four research questions with explicit descriptive null/alternative hypotheses, datasets, holdout design, comparison metrics, observed exploratory evidence and validity threats. It distinguishes original in-sample modelling from later held-out and controlled behavioural scenarios, plus the matched-window forecast comparison.

**Important:** These questions were framed after seeing initial outcomes. They are marked **retrospective exploratory research hypotheses**, not preregistered tests. No unwarranted statistical significance or causal finding is asserted.

## Remaining gates

- [ ] Latest PostgreSQL tests pass including operations, caching and Gemini guard tests.
- [ ] Latest React build/lint pass.
- [ ] Latest Chromium operational-review screenshot and audited resolution pass.
- [ ] Measured 50k request-timing artifact passes validation and is inspected.
- [ ] Live Gemini call with securely configured API key passes independently.
- [ ] After verification, reflect actual evidence in `docs/REMEDIATION_MASTER_PLAN.md`, **without finalizing the university report yet**.

## Technical source

- [Main remediation plan](REMEDIATION_MASTER_PLAN.md)
- [Research hypotheses](RESEARCH_QUESTIONS_HYPOTHESES.md)
- [Operational benchmark workflow](https://github.com/Abhijith513/AI-Finance-System/actions/workflows/operational-benchmarks.yml)
- [Full browser tests](https://github.com/Abhijith513/AI-Finance-System/actions/workflows/presenter-demo.yml)
