# AI Finance System — Verified Architecture and Data Model

**Architecture scope:** source in `Abhijith513/AI-Finance-System`, recovery branch `rescue/submission-critical-fixes` (October 2026). Diagrams describe the actual prototype contracts. They are editable Mermaid source and **not** screenshots or claims of deployed banking infrastructure.

## Figure A — Runtime architecture

```mermaid
flowchart TD
    UI["React + Vite (presenter login, demo, analytics, operations)"]
    AUTH["Django REST token authentication + /api/me + logout revocation"]
    RBAC{"Role and branch permissions"}
    OPS["DRF operational APIs: users, accounts, transactions, alerts, audit"]
    DASH["Dashboard API"]
    REPORT["Management report API"]
    SCREEN["Bounded per-account behavioural screening (heuristic)"]
    DB[("PostgreSQL: original synthetic banking data and derived records")]
    CACHE["Fingerprint + TTL cache for expensive research evaluation"]
    IF["Offline Isolation Forest / statistical benchmark"]
    FORECAST["Seasonal-Naive / SARIMA forecast evaluation"]
    GOOGLE["Optional Gemini qualitative narrative"]
    UI --> AUTH --> RBAC
    RBAC --> OPS
    RBAC --> DASH
    RBAC --> REPORT
    OPS --> DB
    OPS --> SCREEN --> DB
    DASH --> DB
    DASH --> CACHE
    REPORT --> CACHE
    REPORT --> GOOGLE
    CACHE --> IF --> DB
    CACHE --> FORECAST --> DB
```

**Important:** The synchronous live screening path does **not** run Isolation Forest on every transaction. That model belongs to the separately evaluated offline research experiment. Only Admin can run the full guided demo; Admin/Manager can access branch-restricted operational paths; global analytics and AI reporting require Admin/Analyst permissions.

## Figure B — Source-grounded database relationships

```mermaid
erDiagram
    Role ||--o{ User : assigns
    Branch ||--o{ User : contains
    User ||--o{ Account : owns
    Account ||--o{ Transaction : records
    Transaction ||--o{ FraudPrediction : scored
    Transaction ||--o{ Alert : flags
    User ||--o{ AuditLog : performs
    User ||--o{ Report : requests
    Account ||--o{ JournalEntry : legacy_items
    Role {
        int role_id PK
        string role_name
    }
    Branch {
        int branch_id PK
        string branch_name
        string ifsc_code
    }
    User {
        int user_id PK
        string username
        string email UK
        int role_id FK
        int branch_id FK
    }
    Account {
        int account_id PK
        string account_number
        int user_id FK
        decimal balance
    }
    Transaction {
        int transaction_id PK
        int account_id FK
        decimal amount
        string transaction_type
        datetime transaction_time
        int is_anomaly
    }
    FraudPrediction {
        int prediction_id PK
        int transaction_id FK
        decimal fraud_probability
        bool prediction
    }
    Alert {
        int alert_id PK
        int transaction_id FK
        bool is_resolved
    }
    AuditLog {
        int log_id PK
        int user_id FK
        string action
    }
    FinancialForecast {
        int forecast_id PK
        date forecast_month
        decimal predicted_income
        decimal predicted_expense
    }
    Report {
        int report_id PK
        int user_id FK
        string report_type
    }
    JournalEntry {
        int journal_entry_id PK
        int account_id FK
        decimal debit
        decimal credit
    }
```

Notes: The original `JournalEntry` table is historical and does **not** enforce balanced postings; it is not a reliable general ledger. `FinancialForecast` is institution-wide and does not have an account foreign key. A separate balanced synthetic-ledger extension, if accepted, is documented independently and must not be mistaken for the legacy `JournalEntry` records.

## Figure C — Real transaction and alert investigation dataflow

```mermaid
flowchart TD
    START["Authenticated Admin/Manager"] --> ACCOUNT["Select authorized account"]
    ACCOUNT --> POST["POST synthetic transaction"]
    POST --> CHECK{"Account access + payload valid?"}
    CHECK -->|no| REJECT["Reject without writing evidence"]
    CHECK -->|yes| ATOMIC["Atomic database transaction"]
    ATOMIC --> TX["Save immutable transaction"]
    TX --> HISTORY["Read bounded preceding account history"]
    HISTORY --> PRED["Save uncalibrated behavioural score and flag"]
    PRED --> FLAG{"Threshold crossed?"}
    FLAG -->|yes| ALERT["Persist alert"]
    FLAG -->|no| OK["No alert required"]
    ALERT --> AUDIT["Append actor audit event"]
    OK --> AUDIT
    AUDIT --> READ["Re-read transactions, prediction, alerts, audit"]
    READ --> REVIEW{"Authorized review?"}
    REVIEW -->|yes| NOTE["Provide resolution reason"]
    NOTE --> RESOLVE["Atomic alert update + append reasoned audit event"]
    REVIEW -->|no| OPEN["Keep alert open"]
```

## Figure D — Research evaluation versus live operations

```mermaid
flowchart LR
    SEED["Original seed-42 synthetic data"] --> LEGACY["Original 50k in-sample benchmark — preserved"]
    SEED --> TIME["Chronological 80/20 holdout"]
    TIME --> FROZEN["Frozen Isolation Forest test + baseline"]
    BEHAV["Separate 6k behaviour-only synthetic study"] --> TIME2["Independent chronological holdout"]
    TIME2 --> SCORES["Confusion matrices + FP/FN cases"]
    SEED --> SERIES["24 historical monthly points"]
    SERIES --> MATCH["Expanding-window evaluation"]
    MATCH --> PAIRED["Paired months + failures + residual analysis"]
    SEED --> LIVE["Live bounded account screening (separate heuristic)"]
```


## Figure E — Isolated synthetic double-entry extension (Issue 16)

```mermaid
erDiagram
    Account ||--o| SyntheticLedgerAccount : optional_demo_wallet
    User ||--o{ SyntheticLedgerPosting : posts
    SyntheticLedgerPosting ||--|{ SyntheticLedgerLine : has_two_balanced_lines
    SyntheticLedgerAccount ||--o{ SyntheticLedgerLine : debited_or_credited
    SyntheticLedgerPosting o|--o| SyntheticLedgerPosting : reversed_by_once
    SyntheticLedgerAccount {
        bigint id PK
        string code UK
        int account_id FK
        decimal balance
        bool is_system_clearing
    }
    SyntheticLedgerPosting {
        bigint id PK
        string idempotency_key UK
        string request_fingerprint
        string operation
        decimal amount
        int actor_id FK
        int source_account_id FK
        int destination_account_id FK
        bigint reversal_of_id FK
    }
    SyntheticLedgerLine {
        bigint id PK
        bigint posting_id FK
        bigint ledger_account_id FK
        string side
        decimal amount
    }
```

```mermaid
flowchart TD
    A["Authenticated Admin or branch Manager"] --> B{"Authorized source and destination?"}
    B -->|No| DENIED["HTTP 403; no entries"]
    B -->|Yes| KEY{"Same idempotency key?"}
    KEY -->|Existing same request| REPLAY["Return unchanged posting; no duplicate effect"]
    KEY -->|Reused for different request| ERROR["HTTP 400; no changes"]
    KEY -->|New| TX["Atomic PostgreSQL transaction and stable-order wallet locks"]
    TX --> BAL{"Enough balance for debit-normal wallet being credited?"}
    BAL -->|No| ROLLBACK["Rollback posting + lines + audit"]
    BAL -->|Yes| LINES["One debit and one equal credit line"]
    LINES --> APPLY["Update signed synthetic wallet balances"]
    APPLY --> AUDIT["Append actor audit event atomically"]
    AUDIT --> RECON["Admin reconciliation: every pair balanced and wallet sums match lines"]
```

**Isolation boundary:** `SyntheticLedgerPosting`, `SyntheticLedgerLine` and `SyntheticLedgerAccount` are newly introduced teaching tables. Deposits use debit customer demo wallet / credit system clearing; withdrawals reverse those; transfers debit recipient / credit sender; an authorized reversal inverts the original journal legs once. Signed system clearing may be negative, while customer demo wallets reject overdrafts. **No legacy `Account.balance`, `Transaction`, `JournalEntry`, risk benchmark or real money is adjusted by these simulator postings.**

## Figure F — Horizon-specific exploratory forecast intervals (Issue 15)

```mermaid
flowchart LR
  MONTHS["24 synthetic monthly observations"] --> ORIGINS["Rolling, strictly earlier training origins"]
  ORIGINS --> ERROR["Forecast at selected horizon and record absolute errors"]
  ERROR --> N{"At least eight calibration errors?"}
  N -->|No| NA["Uncertainty interval unavailable"]
  N -->|Yes| RANK["Finite-sample ordered error rank at nominal 80%"]
  RANK --> BOUNDS["Seasonal-Naive point forecast ± empirical error radius"]
  BOUNDS --> DISCLOSE["Disclose few validation checks and unverified exchangeability"]
```

Only available horizons are shown with bounds; horizons without sufficient calibration explicitly return `null`. This method is tied to **Seasonal-Naive predictions only**, never silently attached to SARIMA. A nominal interval is *not* evidence of externally validated financial coverage.


## Security and methodological limits

- Passwords must be hashed; token logout revokes the token in Django. Permissions are verified on the server, not only by hiding React tabs.
- Admin and Manager operational permissions are distinct from global Analyst access. Branch access is evaluated on the authoritative account-to-user-to-branch relationship.
- The alert evidence cannot be directly created, deleted or overwritten through normal API operations. Resolution is an audited and reasoned action.
- Research caching has a bounded TTL. A cache hit does not imply scientific revalidation; the original evaluation provenance must be preserved.
- No real bank customers, actual payments, calibrated fraud-risk probabilities, model causal feature explanations, or real-world security certification are claimed.

## Validation requirements

1. Review the Mermaid diagrams against `finance/models.py`, `finance/views.py`, `finance/urls.py`, `frontend/src/DemoExperience.jsx` and `frontend/src/OperationalWorkspace.jsx`.
2. Update diagrams if the isolated balanced ledger introduces new models and APIs.
3. Export genuine diagrams for final report only **after** the version is frozen, with figure numbers and revision SHA.
