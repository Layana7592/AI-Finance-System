# Remediation Issues 13–16 — Acceptance and provenance

**Scope:** Work on the recovery branch only; no changes to the student's original repository, fork main, university report, or original 50,000-row research data until the agreed final review.

## 13 — Architecture / relationship / workflow diagrams

Source: [ARCHITECTURE_ER_DATAFLOW.md](ARCHITECTURE_ER_DATAFLOW.md).
Editable Mermaid diagrams document the real React/Django/PostgreSQL architecture, role authorization, the original database relationships, live transaction and alert dataflow, research-vs-live ML separation, new isolated synthetic ledger ER and posting flow, and rolling forecast uncertainty. The *old* JournalEntry model is accurately marked as unbalanced legacy data; balanced ledger diagrams describe new separate models.

**Acceptance:** schemas/relationships must match actual ORM and migrations; Mermaid syntax must render; export for final report only after the code freeze. Do not invent screenshots or claim deployment.

## 14 — Repeatable latency measurements and model-fit mitigation

Source: [.github/workflows/operational-benchmarks.yml](../.github/workflows/operational-benchmarks.yml).

**Verified baseline (real 50,020 synthetic rows after eight POSTs):** cold dashboard 10,719.51 ms; warm dashboard median 66.21 ms (p95 67.76 ms); operational read median 10.62 ms (p95 12.42 ms); management report median 14.54 ms (p95 15.37 ms); transaction POST median 8.87 ms (p95 10.40 ms); post-write recomputation 10,837.96 ms. Evidence artifact: [run 39025630003](https://github.com/Abhijith513/AI-Finance-System/actions/runs/39025630003).

**What changed:** an explicit dataset-fingerprint/TTL cache shares expensive research evaluations across ordinary dashboard/report visits. Reads of mutable operations remain fresh. The first fit and the first fit after a new transaction remain expensive — this is a disclosed system limitation, not a false claim of universally low latency. Timings use sequential Django APIClient calls on GitHub's Linux runner; they do not measure WAN or concurrency.

## 15 — Forecast uncertainty

Source: `finance/services/forecast_uncertainty.py` and `GET /api/forecast-uncertainty/`.

**Method:** For each prediction horizon, obtain rolling errors from prior synthetic monthly observations; if at least eight non-leaking calibration errors exist, take the finite-sample absolute-error order statistic at nominal 80% and draw a nonnegative Seasonal-Naive interval. Capture calibration count and small prequential coverage diagnostic. With 24 months of history, the longest horizons have insufficient calibration and MUST explicitly return null bounds. Never attach a Seasonal-Naive empirical band to a SARIMA forecast.

**Accepted as:** exploratory uncertainty illustration with explicit unverified exchangeability/coverage limitations, not externally calibrated production forecast intervals. Regression tests confirm only history-supported horizons have bands and horizons without history remain unavailable.

**Acceptance:** migration-independent tests pass; values render visibly with unavailable long horizons in real browser. No arbitrary ±percentage confidence bands.

## 16 — Reconciled synthetic double-entry system

Source: `finance/models.py` and `finance/migrations/0007_synthetic_double_entry_ledger.py`; `finance/services/synthetic_ledger.py`; `finance/ledger_api.py`; `frontend/src/SyntheticLedgerWorkspace.jsx`.

**Isolation:** New `SyntheticLedgerAccount`, `SyntheticLedgerPosting` and `SyntheticLedgerLine` tables ONLY. Existing `Account.balance`, original `Transaction`, existing `JournalEntry`, academic fraud labels, dashboard historical series and forecasts are not touched by ledger postings.

**Rules:** Each committed posting has exactly equal debit and credit values. System clearing is a signed offset; customer demo wallets do not overdraft. Deposits debit wallet / credit system clearing, withdrawals debit system clearing / credit wallet, transfers debit recipient / credit sender. Reversals invert the original legs once. Atomic PostgreSQL transactions and row locks protect updates; globally unique idempotency keys prevent duplicate changes, with conflicting reuse rejected. A successful new posting also appends actor audit evidence. Manager may post only for their own branch; global reconciliation output is Admin-only.

**Acceptance:** Migration runs on clean PostgreSQL; integration tests cover correct double-entry, account and posting balances, retry idempotency, conflicting request, insufficient funds rollback, one-time reversal, cross-branch forbidden access, reconciliation detecting corrupt wallet data, and no change to legacy `Account.balance`. A real Chromium demo must perform a posting and observe the reconciled output. **Not banking-core certification or real money movement.**

## Outstanding checks (do not silently mark closed)

- [ ] Latest ledger migration and tests green.
- [ ] Full 100% backend regression suite green.
- [ ] React production build/lint green.
- [ ] Real browser tests both old and new workflows with ledger/uncertainty screenshots green.
- [ ] Actual, sanitized live Gemini financial report verified with the free-tier secret.
- [ ] Updated latest performance measured after any model-cache changes.
- [ ] Freeze code; compare with Layana's latest repository; only then write the final university report and teach the complete project.

**No handover, merge or final report is authorized by these experimental changes.**
