# Architecture

> **Owner:** Software Architect

## Overview

The ATM Simulator follows a layered architecture separating concerns across API routing,
business logic, data access, and presentation. The system supports two presentation layers:
a React web UI (skeuomorphic ATM kiosk) and a Textual terminal UI. Both communicate with
the same FastAPI backend via REST.

> **See also:** [Frontend Architecture](frontend-architecture.md) for the React state machine,
> component hierarchy, and animation system.

```
┌─────────────────────────────────────────────────┐
│  Presentation Layer                             │
│  ┌──────────────┐  ┌────────────────────────┐  │
│  │ React Web UI │  │ FastAPI (REST API)      │  │
│  │ Textual TUI  │  │                        │  │
│  └──────┬───────┘  └───────────┬────────────┘  │
│─────────┼──────────────────────┼────────────────│
│  Business Logic Layer (services/)               │
│  ┌──────────────┐  ┌──────────┐  ┌──────────┐  │
│  │ auth_service  │  │ txn_svc  │  │ stmt_svc │  │
│  └──────┬───────┘  └────┬─────┘  └────┬─────┘  │
│─────────┼───────────────┼─────────────┼─────────│
│  Data Access Layer (models/ + db/)              │
│  ┌──────────────┐  ┌──────────────────────┐    │
│  │ SQLAlchemy   │  │ Alembic Migrations   │    │
│  └──────┬───────┘  └──────────────────────┘    │
│─────────┼───────────────────────────────────────│
│  ┌──────┴───────┐                               │
│  │ PostgreSQL   │                               │
│  └──────────────┘                               │
└─────────────────────────────────────────────────┘
```

## Admin Dashboard

The ATM Simulator includes a separate React admin dashboard served at `/admin/`. Unlike the ATM
frontend (which uses a state machine for linear screen flow), the admin dashboard uses standard
page-based navigation with independent CRUD views.

**Key differences from the ATM frontend:**

| Aspect | ATM Frontend | Admin Dashboard |
|---|---|---|
| Auth mechanism | `X-Session-ID` header | HTTP-only `admin_session` cookie |
| State management | `useReducer` state machine (17 screens) | `useState` per page |
| Navigation | Deterministic screen flow | Sidebar page switching |
| Animations | Framer Motion spring physics | CSS transitions only |
| Vite base path | `/` (port 5173) | `/admin/` (port 5174) |

**Pages:**
- **Login** — Username/password form with cookie-based session
- **Dashboard** — Stats cards (accounts, activity, maintenance status) with 30s auto-refresh
- **Accounts** — Table with freeze/unfreeze actions per account
- **Audit Logs** — Filterable log table with expandable JSON details
- **Maintenance** — Toggle ATM maintenance mode on/off with optional reason

The admin API endpoints live at `/admin/api/*` and are registered before the SPA catch-all
route, ensuring API calls are never intercepted by the frontend's `index.html` fallback.

**Admin CRUD operations:** The admin dashboard supports full customer and account lifecycle
management. Administrators can create, update, activate, and deactivate customers; create
and close accounts; adjust daily withdrawal and transfer limits; and reset card PINs. All
mutations are recorded in the audit log.

**Data export/import:** The `/admin/api/export` endpoint generates a complete database
snapshot as JSON (customers, accounts, cards, transactions). The `/admin/api/import` endpoint
accepts a snapshot file and supports two conflict resolution strategies: `skip` (preserve
existing records) and `replace` (overwrite with imported data). This enables data migration
between environments and backup/restore workflows.

**S3 snapshot persistence:** When `S3_BUCKET_NAME` is configured, the export endpoint
automatically uploads snapshots to S3 in addition to returning them in the response. The
database seeder can load from an S3 snapshot (via `SEED_SNAPSHOT_S3_KEY`) or a local file
(via `SEED_SNAPSHOT_PATH`) instead of using hardcoded defaults, enabling data recovery
across `terraform destroy` and re-provision cycles.

**Dashboard statistics:** The `/admin/api/dashboard-stats` endpoint returns aggregate
metrics computed via database queries: total customer count, total account count, sum of
all account balances, recent transaction count, and current maintenance mode status. The
admin dashboard polls this endpoint every 30 seconds to keep statistics current.

---

## Technology Decisions

### ADR-001: FastAPI as Web Framework

**Status:** Accepted

**Context:** The ATM simulator requires a Python web framework to expose REST APIs for all
banking operations. Key requirements include request validation, async database access,
automatic API documentation, and high performance for concurrent ATM sessions.

**Decision:** Use FastAPI as the web framework.

**Rationale:**
- **Async-native:** Built on Starlette and ASGI, FastAPI supports `async/await` natively,
  enabling non-blocking database queries and concurrent session handling without threads.
- **Pydantic integration:** Request and response schemas are defined as Pydantic models,
  providing automatic validation, serialization, and type coercion at the API boundary.
  This is critical for a financial application where input validation is a security concern.
- **Auto-generated OpenAPI docs:** FastAPI produces Swagger UI (`/docs`) and ReDoc (`/redoc`)
  endpoints automatically from type annotations. This eliminates documentation drift.
- **Performance:** FastAPI consistently benchmarks among the fastest Python web frameworks,
  important for the concurrent transaction safety requirements (E2E-ERR-02).
- **Dependency injection:** FastAPI's `Depends()` system cleanly manages database sessions,
  authentication state, and service dependencies without global state.

**Consequences:**
- Requires Python 3.10+ for full type hint support.
- Team must understand async/await patterns and avoid blocking calls in route handlers.
- Testing requires `httpx.AsyncClient` (via `pytest-asyncio`) rather than synchronous test
  clients.

---

### ADR-002: PostgreSQL (Production) + SQLite (Development/Test)

**Status:** Accepted

**Context:** The application handles financial transactions requiring ACID guarantees,
concurrent access safety, and relational integrity. However, local development and CI
should not require a running PostgreSQL instance.

**Decision:** Use PostgreSQL 16 for production and Docker-based development; use SQLite for
unit tests and lightweight local development.

**Rationale:**
- **PostgreSQL for production:** Full ACID compliance, row-level locking for concurrent
  withdrawals (E2E-ERR-02), robust `DECIMAL` type support, JSON columns for audit log
  details, and mature tooling.
- **SQLite for testing:** Zero-configuration, in-memory or file-based databases that are
  created and destroyed per test run. This enables fast, isolated test execution without
  external dependencies.
- **SQLAlchemy abstraction:** SQLAlchemy's dialect system allows the same ORM code to run
  against both databases. Schema differences (e.g., `JSON` column behavior) are handled
  by SQLAlchemy's cross-dialect compatibility layer.

**Consequences:**
- Some PostgreSQL-specific features (e.g., `FOR UPDATE` row locking) must be tested
  separately in integration tests against a real PostgreSQL instance.
- The `JSON` column type must use SQLAlchemy's generic `JSON` rather than
  `sqlalchemy.dialects.postgresql.JSON` to maintain SQLite compatibility.
- Alembic migrations target PostgreSQL; SQLite test databases use `create_all()` instead.

---

### ADR-003: SQLAlchemy 2.0 with Alembic Migrations

**Status:** Accepted

**Context:** The data model includes five interrelated entities with foreign keys,
constraints, and computed properties. Schema evolution must be tracked and reproducible.

**Decision:** Use SQLAlchemy 2.0 (mapped column style) as the ORM with Alembic for
database migrations.

**Rationale:**
- **Type-safe ORM:** SQLAlchemy 2.0's `Mapped[]` annotations provide full type safety,
  catching column type mismatches at static analysis time via mypy.
- **Declarative models:** Models serve as both the database schema definition and the
  Python domain objects, reducing mapping boilerplate.
- **Alembic migrations:** Schema changes are tracked as versioned migration scripts,
  enabling reliable database upgrades in production without data loss.
- **Async support:** SQLAlchemy 2.0 supports async sessions via `asyncpg`, aligning with
  FastAPI's async-first design.
- **Mature ecosystem:** Extensive documentation, community support, and battle-tested in
  production financial systems.

**Consequences:**
- Team must use SQLAlchemy 2.0 style (`mapped_column`, `Mapped[]`) rather than legacy
  1.x `Column()` style.
- Alembic migrations must be generated and reviewed for every schema change.
- Async database sessions require careful lifecycle management (no lazy loading across
  request boundaries).

---

### ADR-004: Integer Cents for Monetary Values

**Status:** Accepted

**Context:** Financial calculations require exact precision. Floating-point arithmetic
introduces rounding errors that are unacceptable for monetary values (e.g.,
`0.1 + 0.2 != 0.3` in IEEE 754).

**Decision:** Store all monetary values as integer cents in the database and application
layer. Use `Decimal` for intermediate calculations where needed. Convert to dollar display
format only at the presentation layer.

**Rationale:**
- **No rounding errors:** Integer arithmetic is exact. `$5,250.00` is stored as `525000`
  cents, eliminating all floating-point precision issues.
- **Database compatibility:** Integer columns are universally supported, fast to index,
  and have no precision/scale configuration to get wrong.
- **Comparison safety:** Integer equality (`==`) is reliable, unlike float equality which
  requires epsilon comparisons.
- **Industry standard:** Most payment systems (Stripe, bank core systems) use integer
  minor units internally.

**Consequences:**
- All API request schemas accept `amount_cents` (integer), not dollar amounts.
- Display formatting (`$1,234.56`) is applied only in Pydantic response schemas and UI
  templates via `formatting.py` utilities.
- Test assertions use exact integer comparisons (`assert balance_cents == 525000`), never
  approximate float comparisons.

---

### ADR-005: Opaque Server-Side Session Tokens

**Status:** Accepted

**Context:** After PIN authentication, the user needs a session token to authorize
subsequent operations. The token design affects security, scalability, and simplicity.

**Decision:** Use opaque server-side session tokens generated via `secrets.token_urlsafe(32)`
rather than JWTs.

**Rationale:**
- **Immediate revocation:** Server-side sessions can be invalidated instantly on logout or
  lockout. JWTs remain valid until expiration, requiring complex revocation lists.
- **No sensitive data in tokens:** Opaque tokens encode nothing — they are random strings
  used as lookup keys. JWTs contain claims that, if the signing key is compromised, expose
  user data.
- **Simpler implementation:** No key management, no token refresh logic, no signature
  verification. A single database/cache lookup validates the session.
- **ATM-appropriate:** Real ATMs use server-side sessions. The simulator should model this
  accurately. ATM sessions are short-lived (2-minute timeout) and single-device, making
  JWT's stateless scaling advantages irrelevant.

**Consequences:**
- Every authenticated API call requires a session lookup (database or cache query).
- Session state (creation time, last activity, associated account) is stored server-side.
- Horizontal scaling requires shared session storage (Redis in Phase 2).

---

### ADR-006: Layered Architecture (API -> Service -> Repository)

**Status:** Accepted

**Context:** The application must separate concerns cleanly to enable independent testing,
security review, and team collaboration. Business rules (daily limits, hold policies)
must be isolated from HTTP handling and database access.

**Decision:** Adopt a three-layer architecture: API (routing + validation), Service
(business logic), and Data Access (ORM models + queries).

**Rationale:**
- **Testability:** Services can be unit-tested with mocked database sessions. API routes
  can be integration-tested with a real database. Each layer has a clear test strategy.
- **Security boundary:** The API layer handles all input validation (Pydantic schemas) and
  authentication (session verification). Services trust their inputs are validated.
- **Single responsibility:** Route handlers do only: parse request, call service, format
  response. Services do only: enforce business rules, coordinate data access. Models do
  only: define schema, provide computed properties.
- **Team ownership:** The Backend Engineer owns `api/` and `services/`. The Architect owns
  `models/` and `schemas/`. The Security Engineer reviews `services/` and `utils/security.py`.
  Clear boundaries reduce merge conflicts.

**Consequences:**
- No business logic in route handlers (no balance checks, no limit enforcement in `api/`).
- No HTTP concerns in services (no status codes, no request/response objects in `services/`).
- Services receive and return plain Python types or model instances, not Pydantic schemas.

---

## Data Model

The ATM Simulator data model consists of five core entities designed to represent customers,
their accounts, financial transactions, ATM cards, and a complete audit trail.

### Entity Relationship Diagram

```
┌─────────────────────┐         ┌──────────────────────────┐
│      Customer        │         │         Account           │
├─────────────────────┤    1:N  ├──────────────────────────┤
│ id (PK)             │────────<│ id (PK)                  │
│ first_name          │         │ customer_id (FK) [idx]   │
│ last_name           │         │ account_number (unique)  │
│ date_of_birth       │         │ account_type (enum)      │
│ email               │         │ balance_cents (int)      │
│ phone               │         │ available_balance_cents   │
│ created_at          │         │ daily_withdrawal_used     │
│ updated_at          │         │ daily_transfer_used       │
│ is_active           │         │ status (enum)            │
└─────────────────────┘         │ created_at / updated_at  │
                                └───────┬──────────────────┘
                                        │
                          ┌─────────────┼─────────────┐
                          │ 1:N         │ 1:N         │ 1:N
                 ┌────────┴───────┐  ┌──┴──────────┐  │
                 │  Transaction    │  │   ATM_Card   │  │
                 ├────────────────┤  ├─────────────┤  │
                 │ id (PK)        │  │ id (PK)     │  │
                 │ account_id (FK)│  │ account_id  │  │
                 │ txn_type (enum)│  │ card_number │  │
                 │ amount_cents   │  │ pin_hash    │  │
                 │ balance_after  │  │ failed_atts │  │
                 │ reference_num  │  │ locked_until│  │
                 │ description    │  │ is_active   │  │
                 │ related_acct_id│  └─────────────┘  │
                 │ hold_until     │                    │
                 │ created_at     │         ┌──────────┴──────┐
                 └────────────────┘         │    Audit_Log     │
                                            ├─────────────────┤
                                            │ id (PK)         │
                                            │ event_type (enum│
                                            │ account_id (FK) │
                                            │ ip_address      │
                                            │ session_id      │
                                            │ details (JSON)  │
                                            │ created_at [idx]│
                                            └─────────────────┘
```

### Entity Descriptions

#### Customer
Represents a bank customer who may hold one or more accounts. Stores personal information
required for statement generation and account identification. The `is_active` flag allows
soft-deletion without losing transaction history.

#### Account
Represents a single bank account (checking or savings). Key design decisions:
- **Dual balance fields:** `balance_cents` is the total ledger balance; `available_balance_cents`
  reflects holds from check deposits and pending transactions. This distinction is critical
  for the deposit hold policy (first $200 immediately available, remainder held).
- **Daily usage tracking:** `daily_withdrawal_used_cents` and `daily_transfer_used_cents`
  track cumulative daily usage against configurable limits ($500 and $2,500 respectively).
  These fields reset at the start of each business day.
- **Status enum:** `ACTIVE`, `FROZEN`, `CLOSED`. Frozen accounts reject all transactions
  but allow balance inquiries. Closed accounts reject all operations.

#### Transaction
Records every financial operation against an account. Each transaction captures the
`balance_after` to enable running balance calculations on statements without re-computing
from the beginning of time. The `related_account_id` field links the two sides of a
transfer (the TRANSFER_OUT on the source account references the destination, and vice versa).
The `hold_until` field tracks when deposited funds become fully available.

#### ATM_Card
Represents a physical ATM card linked to an account. Stores the bcrypt-hashed PIN (with
application-level pepper), tracks consecutive failed authentication attempts, and manages
lockout state. The `locked_until` timestamp is set when `failed_attempts` reaches the
configured maximum (default 3), enforcing a 30-minute lockout period.

#### Audit_Log
An append-only log of all security-relevant events. The `event_type` enum categorizes
events (authentication, transactions, PIN changes, administrative actions). The `details`
JSON column stores event-specific structured data without requiring schema changes for
new event types. The `account_id` is nullable to support pre-authentication events (e.g.,
failed login with an unknown card number).

### Key Relationships
- **Customer -> Account:** One-to-many. A customer may have multiple accounts (e.g., Alice
  has both checking and savings).
- **Account -> Transaction:** One-to-many. Transactions are ordered by `created_at DESC`
  for mini-statement display.
- **Account -> ATM_Card:** One-to-many. Supports card replacement without losing account
  history.
- **Account -> Audit_Log:** One-to-many (nullable FK). Enables filtering audit history by
  account.

---

## API Design Philosophy

The API follows REST conventions with a `/api/v1/` prefix for versioning. All endpoints
accept and return JSON. Key design principles:

1. **Validation at the boundary.** Every request is validated by a Pydantic schema before
   reaching the service layer. Invalid requests receive a `422 Unprocessable Entity` response
   with detailed error information.

2. **Consistent error responses.** All errors return an `ErrorResponse` schema with `error`
   (category), `detail` (human-readable message), and `error_code` (machine-readable code).
   This enables clients to handle errors programmatically.

3. **Session-based authentication.** All endpoints except `/api/v1/auth/login` and `/health`
   require an `X-Session-ID` header. Invalid or expired sessions receive a `401 Unauthorized`
   response.

4. **Amounts in cents.** All monetary values in request and response bodies are expressed in
   integer cents to avoid floating-point issues. Display-formatted dollar strings (e.g.,
   `"$1,234.56"`) are provided as convenience fields in response schemas.

5. **Idempotency.** Transaction endpoints return a `reference_number` that uniquely identifies
   each operation. Clients can use this for reconciliation and duplicate detection.

6. **No sensitive data in responses.** Account numbers are masked (last 4 digits only).
   PINs are never included in any response. Error messages for authentication failures are
   deliberately generic to prevent enumeration attacks.

## Security Architecture & Threat Model

> **Owner:** Security Engineer

This section documents the security controls, threat model, and design decisions for
the ATM Simulator. Although this is a simulator, security is treated as if real money
is at stake.

### Authentication Threats

| Threat | Risk | Mitigation |
|---|---|---|
| **Brute-force PIN guessing** | High — 4-digit PINs have only 10,000 combinations | 3 failed attempts lock the card for 30 minutes; rate limit of 5 attempts per card per 15-minute window at the API layer |
| **Credential stuffing** | Medium — attackers may try known card/PIN pairs from breaches | Lockout policy applies per card number; generic error messages ("authentication failed") reveal nothing about whether the card number exists |
| **PIN interception (shoulder surfing / logging)** | Medium | PINs are never logged, not even in masked form; bcrypt hashing with pepper ensures stored PINs are unrecoverable; session tokens replace PINs after initial auth |
| **Offline hash cracking** | Low-Medium — if database is compromised | bcrypt with cost factor 12 makes brute-force infeasible (~250ms per attempt); application-level pepper adds a second secret not stored in the database |

### Session Management

| Threat | Risk | Mitigation |
|---|---|---|
| **Session hijacking** | Medium | Tokens generated via `secrets.token_urlsafe(32)` (256 bits of entropy); tokens are opaque and unguessable |
| **Session fixation** | Low | New token issued on every successful authentication; old tokens cannot be reused |
| **Stale sessions** | Medium — unattended ATM with active session | Automatic 2-minute inactivity timeout enforced server-side; all operations validate session freshness |

Session tokens are:
- Cryptographically random (256-bit entropy via `secrets.token_urlsafe`).
- Opaque — they encode no user data and cannot be decoded.
- Short-lived — 2-minute inactivity timeout, enforced on every API call.
- Single-use per session — a new token is issued at login; logout invalidates it.

### Injection Attacks

| Threat | Risk | Mitigation |
|---|---|---|
| **SQL injection** | Critical if exploited | SQLAlchemy ORM with parameterized queries exclusively; no raw SQL anywhere in the codebase; Pydantic validation rejects unexpected input shapes before they reach the data layer |
| **Cross-site scripting (XSS)** | Medium (web UI) | `sanitize_input()` escapes HTML special characters (`<`, `>`, `&`, `"`, `'`); Pydantic schemas enforce strict types at the API boundary |
| **Command injection** | Low | No shell execution in the application; all external operations use library APIs, not subprocess calls |
| **Null byte injection** | Low | `sanitize_input()` strips null bytes from all user-provided strings |

### Data Protection

#### PIN Storage
- PINs are hashed using **bcrypt** with a cost factor of **12** (~250ms per hash).
- An **application-level pepper** is prepended to the PIN before hashing. The pepper
  is stored as an environment variable (`PIN_PEPPER`), separate from the database.
- Even if the database is fully compromised, the pepper must also be obtained to
  attempt offline cracking — defense in depth.
- PINs are **never logged** — not plaintext, not masked, not hashed. Log entries
  reference only card/account identifiers.

#### Account Number Masking
- All user-facing output masks account numbers, showing only the last 4 digits.
- Example: `1000-0001-0001` is displayed as `****-****-0001`.
- Masking is applied at the presentation layer via `mask_account_number()`.
- Internal logs that require account identification use the full number but are
  restricted to audit logs with appropriate access controls.

#### Monetary Values
- All monetary amounts are stored as integer cents (`Decimal` in Python, integer in DB)
  to prevent floating-point rounding errors.
- Dollar formatting occurs only at the presentation layer.

### Input Validation Strategy

Input validation follows a **two-layer defense-in-depth** approach:

1. **Pydantic schemas (API boundary):** Every API endpoint uses Pydantic models for
   request validation. This is the primary validation layer — it enforces types,
   value ranges, string patterns, and required fields. Invalid requests are rejected
   with a 422 response before reaching business logic.

2. **`sanitize_input()` (defense-in-depth):** An additional sanitization function
   strips whitespace, removes null bytes, and escapes HTML special characters. This
   guards against edge cases that pass Pydantic validation but contain potentially
   dangerous content.

Business logic in the `services/` layer trusts that inputs have been validated by the
API layer. Services do not re-validate types or formats — they enforce **business rules**
(e.g., sufficient funds, daily limits, account status).

### Audit Logging Requirements

The audit log captures a complete, tamper-evident record of all security-relevant events.

#### Events Logged

| Event Category | Specific Events | Data Captured |
|---|---|---|
| **Authentication** | Login success, login failure, account lockout, lockout expiry | Card number (full), timestamp, IP address, session ID, failure reason (generic) |
| **Session lifecycle** | Session created, session expired (timeout), session terminated (logout) | Session ID, account ID, timestamp, duration |
| **Transactions** | Withdrawal, deposit, transfer — both success and failure | Account ID, amount, transaction type, reference number, result, failure reason |
| **PIN management** | PIN change success, PIN change failure | Account ID, timestamp, failure reason (never the PIN itself) |
| **Administrative** | Account freeze/unfreeze, limit changes, account creation | Admin ID, target account, action, old/new values |

#### What Is Never Logged
- PIN values (plaintext, masked, or hashed)
- Session token values
- Full request/response bodies containing sensitive fields

#### Log Format
All audit log entries are stored in the `audit_log` database table with:
- `event_type`: Enumerated event category
- `account_id`: Foreign key to the affected account (nullable for failed auth on unknown cards)
- `ip_address`: Client IP for forensic correlation
- `session_id`: Session identifier for grouping related events
- `details`: JSON field for event-specific structured data
- `created_at`: Server-side timestamp (not client-provided)
