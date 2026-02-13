# ATM Simulator — Claude Agent Teams Project Guide

## Project Overview

Build a full-featured **Python ATM (Automated Teller Machine) simulator** that replicates real-world ATM functionality. The application should feel authentic — PIN authentication, account management, transaction processing, receipt/statement generation, and proper audit logging — as if it were a prototype for an actual bank kiosk.

### Development Philosophy

- **Start small, grow deliberately.** Phase 1 runs on a local Docker container. Only after the application is fully functional and tested do we move to cloud hosting.
- **Security-first thinking.** Even though this is a simulator, treat it as if real money is at stake. Hash PINs, validate inputs, log everything, handle edge cases.
- **Production-grade quality.** Clean code, comprehensive tests, proper documentation. This is a portfolio-quality project.

---

## Agent Team Structure

### Recommended Team Composition (8 Agents)

| Agent Role | Responsibility | Key Deliverables |
|---|---|---|
| **Team Lead** | Orchestration, task decomposition, integration review, conflict resolution | Task list, sprint plans, final integration |
| **Software Architect** | System design, API contracts, data models, technology decisions | Architecture docs, ERD, API specs, ADRs |
| **UX Designer** | User interface design, interaction flows, accessibility, error messaging | Wireframes, UI component specs, user flow diagrams |
| **Software Engineer (Backend)** | Core business logic, API endpoints, database layer, transaction engine | Application source code, database migrations |
| **Software Engineer (Frontend/UX)** | React web UI, component development, animations, state management | React components, CSS, Framer Motion animations, frontend tests |
| **Software Engineer in Test (SDET)** | Test strategy, unit/integration/E2E tests, load testing, security testing | Test suite, coverage reports, test plans |
| **Security Engineer** | Authentication, encryption, input validation, audit logging, threat modeling | Security review, threat model, hardening checklist |
| **DevOps / Cloud Engineer** | Docker configuration, CI/CD pipeline, cloud deployment, monitoring | Dockerfile, docker-compose, deployment configs, IaC |

> **Note on the Technical Writer role:** Rather than a dedicated agent, technical writing responsibilities (README, API docs, user guide) should be distributed. The Architect owns API documentation, the UX Designer owns the user guide, and the DevOps Engineer owns deployment/ops documentation. The Team Lead synthesizes the final README. This avoids a bottleneck agent with idle time during core development.

### Agent Coordination Rules

1. **File ownership is sacred.** Each agent owns specific directories/files. No two agents should edit the same file simultaneously. If cross-cutting changes are needed, sequence them with task dependencies.
2. **Plan before implementing.** Every agent should submit a plan for lead approval before writing code, especially for tasks touching shared interfaces (API contracts, database schema, shared utilities).
3. **Use the shared task list.** All work items flow through the team's task system. No ad-hoc side work.
4. **Communicate interface changes immediately.** If an agent needs to change an API contract, data model, or shared config, message the lead and affected agents first.

---

## Technical Stack

### Core Application

| Component | Technology | Rationale |
|---|---|---|
| Language | Python 3.12+ | Project requirement |
| Web Framework | FastAPI | Async support, automatic OpenAPI docs, Pydantic validation, modern Python |
| Database | PostgreSQL 16 (production), SQLite (local dev/testing) | Relational integrity for financial data; SQLite for zero-config local development |
| ORM | SQLAlchemy 2.0 + Alembic | Mature, well-documented, migration support |
| PDF Generation | ReportLab | Industry standard for Python PDF generation |
| Authentication | PIN-based with bcrypt hashing | Simulates real ATM auth; bcrypt for secure storage |
| Terminal UI | Textual | Terminal-based ATM simulation feel (Phase 1) |
| Web UI | React 18 + Vite + TypeScript (strict) | Skeuomorphic ATM web interface (Phase 4/v2.0) |
| Animations | Framer Motion 11 | Spring physics, AnimatePresence screen transitions, orchestrated sequences |
| HTTP Client | Axios | Request/response interceptors for session headers, 401/503 handling |
| State Management | React Context + useReducer | State machine pattern for linear ATM flow; no external deps needed |
| Task Queue | Celery + Redis | Async operations (PDF generation, background tasks) |

### Infrastructure

| Component | Technology | Rationale |
|---|---|---|
| Containerization | Docker + docker-compose | Local development consistency |
| CI/CD | GitHub Actions | Free for public repos, excellent Docker support |
| Python Testing | pytest + pytest-cov + pytest-asyncio | Python testing standard |
| Frontend Testing | Vitest + React Testing Library + Playwright | Unit/component tests (Vitest), browser E2E (Playwright) |
| Python Linting | Ruff | Fast, replaces flake8 + black + isort |
| Frontend Linting | ESLint (strict) + TypeScript strict mode | Zero-warning policy, strict type checking |
| Python Type Checking | mypy (strict mode) | Catch bugs early, especially important for financial logic |
| API Documentation | Auto-generated via FastAPI/OpenAPI | Zero-effort, always in sync |
| Python Security | Bandit + pip-audit | SAST + dependency vulnerability scanning |
| Frontend Security | npm audit | Dependency vulnerability scanning |
| Container Security | Trivy | Docker image + Terraform IaC scanning |
| Secret Detection | Gitleaks | Leaked credentials in git history |
| Dependency Updates | Dependabot | Automated PRs for vulnerable dependencies |
| Cloud Hosting (Phase 3) | AWS (ECS Fargate or App Runner) | Better fit than Vercel for a Python backend with database |

> **Why AWS over Vercel?** Vercel is optimized for frontend/Next.js deployments. A Python application with a PostgreSQL database, background jobs, and persistent state is a much better fit for AWS. Alternatives: Railway or Render for simpler deployment if full AWS is overkill.

---

## Feature Requirements

### Core ATM Operations

#### 1. Authentication
- Card number (simulated as account number) + 4-6 digit PIN
- Three failed attempts → account lockout (30-minute cooldown)
- Session timeout after 2 minutes of inactivity
- Secure PIN change flow (verify old PIN → enter new PIN → confirm new PIN)

#### 2. Balance Inquiry
- Display current available balance and total balance (including holds)
- Show last 5 transactions as a mini-statement
- Option to print to receipt (PDF)

#### 3. Cash Withdrawal
- Predefined quick-withdraw amounts ($20, $40, $60, $100, $200)
- Custom amount entry (multiples of $20 only, simulating bill denominations)
- Daily withdrawal limit enforcement ($500 default)
- Insufficient funds handling with clear messaging
- Overdraft protection option (if linked savings account exists)
- Dispense confirmation with denomination breakdown

#### 4. Cash Deposit
- Accept deposit amount entry
- Simulate envelope deposit (immediate hold) vs. cash deposit (partial immediate availability)
- Generate deposit receipt with reference number
- Hold policy: first $200 available immediately, remainder after 1 business day

#### 5. Check Deposit
- Accept check amount and check number
- Apply hold policy: first $200 available next business day, remainder after 2 business days
- Generate deposit receipt

#### 6. Fund Transfer
- Transfer between user's own accounts (checking ↔ savings)
- Transfer to another account (by account number)
- Daily transfer limit enforcement ($2,500 default)
- Confirmation screen with source, destination, amount before execution
- Transfer receipt generation

#### 7. Account Statement
- Generate PDF statement for selectable date range (7 days, 30 days, 90 days, custom)
- Statement includes: account holder name, account number (masked), opening/closing balance, all transactions with dates and running balance, summary totals
- Save PDF to configurable output directory

#### 8. PIN Management
- Change PIN (requires current PIN verification)
- PIN complexity rules: no sequential digits (1234), no repeated digits (1111), no birthdate patterns

### Administrative Features (Implemented in Phase 2)

- Admin panel: create/deactivate accounts, adjust limits, view audit logs
- ATM maintenance mode: temporarily disable operations (Redis flag, 503 middleware)
- Cash cassette simulation: track available denominations, go out-of-service when empty
- Rate limiting (slowapi): 5 auth attempts per card per 15 minutes
- Structured JSON logging with correlation IDs
- Health check endpoints (`/health`, `/ready`)

---

## Data Model

### Core Entities

```
┌─────────────────────┐     ┌──────────────────────┐
│      Customer        │     │       Account         │
├─────────────────────┤     ├──────────────────────┤
│ id (PK)             │────<│ id (PK)              │
│ first_name          │     │ customer_id (FK)     │
│ last_name           │     │ account_number       │
│ date_of_birth       │     │ account_type (enum)  │
│ email               │     │ balance              │
│ phone               │     │ available_balance    │
│ created_at          │     │ daily_withdrawal_used│
│ updated_at          │     │ daily_transfer_used  │
│ is_active           │     │ status (enum)        │
└─────────────────────┘     │ created_at           │
                            │ updated_at           │
                            └──────────┬───────────┘
                                       │
                            ┌──────────┴───────────┐
                            │     Transaction       │
                            ├──────────────────────┤
                            │ id (PK)              │
                            │ account_id (FK)      │
                            │ transaction_type     │
                            │ amount               │
                            │ balance_after        │
                            │ reference_number     │
                            │ description          │
                            │ related_account_id   │
                            │ hold_until           │
                            │ created_at           │
                            └──────────────────────┘

┌─────────────────────┐     ┌──────────────────────┐
│    ATM_Card          │     │     Audit_Log         │
├─────────────────────┤     ├──────────────────────┤
│ id (PK)             │     │ id (PK)              │
│ account_id (FK)     │     │ event_type           │
│ card_number         │     │ account_id (FK, null)│
│ pin_hash            │     │ ip_address           │
│ failed_attempts     │     │ session_id           │
│ locked_until        │     │ details (JSON)       │
│ is_active           │     │ created_at           │
│ created_at          │     └──────────────────────┘
│ updated_at          │
└─────────────────────┘
```

### Key Enums
- **account_type:** CHECKING, SAVINGS
- **account_status:** ACTIVE, FROZEN, CLOSED
- **transaction_type:** WITHDRAWAL, DEPOSIT_CASH, DEPOSIT_CHECK, TRANSFER_IN, TRANSFER_OUT, FEE, INTEREST

---

## Project Structure

```
atm-simulator/
├── CLAUDE.md                    # This file — agent team instructions
├── README.md                    # Project overview, setup, usage
├── LICENSE
├── pyproject.toml               # Project metadata, dependencies, tool config
├── Dockerfile
├── docker-compose.yml           # App + PostgreSQL + (Phase 2) Redis
├── .env.example                 # Environment variable template
├── frontend/                    # React web UI (v2.0)
│   ├── package.json
│   ├── vite.config.ts           # Vite + Vitest config with coverage thresholds
│   ├── tsconfig.json            # TypeScript strict mode
│   ├── eslint.config.js
│   ├── index.html
│   └── src/
│       ├── main.tsx             # Entry point
│       ├── App.tsx              # Screen router (state machine switch)
│       ├── api/                 # Axios client + typed endpoint functions
│       ├── state/               # React Context + useReducer state machine
│       ├── hooks/               # Custom hooks (useATMContext, useIdleTimer)
│       ├── components/
│       │   ├── atm-housing/     # ATMFrame, ScreenBezel, SideButtons, Keypad, etc.
│       │   ├── screens/         # 17 screen components
│       │   └── shared/          # Reusable display components
│       ├── styles/              # CSS (metallic gradients, CRT glow, keypad)
│       └── __tests__/           # Vitest component + hook + API tests
├── .github/
│   └── workflows/
│       ├── ci.yml               # Python + Frontend lint, type-check, test on every PR
│       └── deploy.yml           # (Phase 3) Deploy to AWS
├── alembic/                     # Database migrations
│   ├── alembic.ini
│   └── versions/
├── src/
│   └── atm/
│       ├── __init__.py
│       ├── main.py              # FastAPI app factory
│       ├── config.py            # Settings via pydantic-settings
│       ├── models/              # SQLAlchemy models
│       │   ├── __init__.py
│       │   ├── customer.py
│       │   ├── account.py
│       │   ├── transaction.py
│       │   ├── card.py
│       │   └── audit.py
│       ├── schemas/             # Pydantic request/response schemas
│       │   ├── __init__.py
│       │   ├── auth.py
│       │   ├── account.py
│       │   └── transaction.py
│       ├── api/                 # FastAPI routers
│       │   ├── __init__.py
│       │   ├── auth.py
│       │   ├── accounts.py
│       │   ├── transactions.py
│       │   └── statements.py
│       ├── services/            # Business logic layer
│       │   ├── __init__.py
│       │   ├── auth_service.py
│       │   ├── account_service.py
│       │   ├── transaction_service.py
│       │   ├── statement_service.py
│       │   └── audit_service.py
│       ├── db/                  # Database setup
│       │   ├── __init__.py
│       │   ├── session.py
│       │   └── seed.py          # Sample data for development
│       ├── ui/                  # Textual terminal UI
│       │   ├── __init__.py
│       │   ├── app.py
│       │   └── screens/
│       │       ├── welcome.py
│       │       ├── pin_entry.py
│       │       ├── main_menu.py
│       │       ├── withdrawal.py
│       │       ├── deposit.py
│       │       ├── transfer.py
│       │       └── statement.py
│       ├── pdf/                 # PDF generation
│       │   ├── __init__.py
│       │   └── statement_generator.py
│       └── utils/
│           ├── __init__.py
│           ├── security.py      # PIN hashing, input sanitization
│           └── formatting.py    # Currency formatting, masking
├── tests/
│   ├── conftest.py              # Shared fixtures: test DB, async client, seed data
│   ├── factories.py             # Factory functions for test data generation
│   ├── COVERAGE_EXCLUSIONS.md   # Log of all coverage exclusions with justifications
│   ├── unit/
│   │   ├── services/
│   │   │   ├── test_auth_service.py
│   │   │   ├── test_transaction_service.py
│   │   │   ├── test_account_service.py
│   │   │   ├── test_statement_service.py
│   │   │   └── test_audit_service.py
│   │   ├── utils/
│   │   │   ├── test_security.py
│   │   │   └── test_formatting.py
│   │   ├── schemas/
│   │   │   ├── test_auth_schemas.py
│   │   │   ├── test_account_schemas.py
│   │   │   └── test_transaction_schemas.py
│   │   └── models/
│   │       ├── test_customer_model.py
│   │       ├── test_account_model.py
│   │       ├── test_transaction_model.py
│   │       └── test_card_model.py
│   ├── integration/
│   │   ├── test_auth_api.py
│   │   ├── test_withdrawal_api.py
│   │   ├── test_deposit_api.py
│   │   ├── test_transfer_api.py
│   │   ├── test_statement_api.py
│   │   ├── test_balance_api.py
│   │   └── test_pin_management_api.py
│   └── e2e/                     # 42 E2E tests across 8 categories
│       ├── test_auth_journeys.py
│       ├── test_withdrawal_journeys.py
│       ├── test_deposit_journeys.py
│       ├── test_transfer_journeys.py
│       ├── test_statement_journeys.py
│       ├── test_balance_journeys.py
│       ├── test_compound_journeys.py
│       └── test_error_journeys.py
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── deployment.md
│   └── user-guide.md
└── scripts/
    ├── seed_db.py               # Populate dev database
    └── generate_sample_statement.py
```

### File Ownership by Agent

| Directory / File | Primary Owner | May Consult |
|---|---|---|
| `src/atm/models/` | Architect | Backend Engineer |
| `src/atm/schemas/` | Architect | Backend Engineer |
| `src/atm/api/` | Backend Engineer | Architect |
| `src/atm/services/` | Backend Engineer | Security Engineer |
| `src/atm/ui/` | UX Designer | Backend Engineer |
| `frontend/src/components/` | Frontend Engineer | UX Designer |
| `frontend/src/state/` | Frontend Engineer | Architect |
| `frontend/src/api/` | Frontend Engineer | Backend Engineer |
| `frontend/src/hooks/` | Frontend Engineer | — |
| `frontend/src/styles/` | Frontend Engineer | UX Designer |
| `frontend/src/__tests__/` | SDET | Frontend Engineer |
| `src/atm/pdf/` | Backend Engineer | UX Designer |
| `src/atm/utils/security.py` | Security Engineer | Backend Engineer |
| `src/atm/db/` | Backend Engineer | Architect |
| `tests/` | SDET | Backend Engineer |
| `tests/COVERAGE_EXCLUSIONS.md` | SDET | Team Lead (reviewer) |
| `Dockerfile`, `docker-compose.yml` | DevOps Engineer | Architect |
| `.github/workflows/` | DevOps Engineer | SDET |
| `docs/architecture.md` | Architect | — |
| `docs/api.md` | Architect | Backend Engineer |
| `docs/deployment.md` | DevOps Engineer | — |
| `docs/user-guide.md` | UX Designer | — |
| `alembic/` | Backend Engineer | Architect |
| `CLAUDE.md`, `README.md` | Team Lead | All |

---

## Development Phases

### Phase 1: Local Docker (MVP)

**Goal:** A fully functional ATM simulator running in Docker with all core operations working against a local PostgreSQL database.

**Sprint 1 — Foundation (Architect + DevOps + Security)**
1. Architect: Define data models, API contracts (OpenAPI spec), and write Architecture Decision Records (ADRs)
2. DevOps: Create Dockerfile, docker-compose.yml (app + PostgreSQL), .env configuration
3. Security: Define authentication flow, PIN hashing strategy, session management approach, threat model
4. **Gate:** Team Lead reviews and approves all design documents before implementation begins

**Sprint 2 — Core Backend (Backend Engineer + SDET)**
1. Backend: Implement models, database migrations, seed data
2. Backend: Build auth service (PIN verification, lockout, sessions)
3. Backend: Build transaction service (withdrawal, deposit logic with hold policies)
4. SDET: Write test fixtures, unit tests for auth and transaction services
5. **Gate:** All services pass unit tests with 100% coverage on `services/` and `utils/security.py`, 95%+ overall

**Sprint 3 — API + Transfer + Statements (Backend + SDET + UX)**
1. Backend: Implement FastAPI routers for all operations
2. Backend: Build transfer service with limit enforcement
3. Backend: Build PDF statement generator
4. SDET: Write integration tests for all API endpoints
5. UX: Design terminal UI screens and interaction flow
6. **Gate:** All API endpoints working, integration tests passing

**Sprint 4 — UI + Polish + Security Review (UX + Security + SDET)**
1. UX: Implement Textual terminal UI connecting to API
2. Security: Conduct security review — input validation, SQL injection, PIN handling, audit logging
3. SDET: Write E2E tests (full user journeys), edge case tests
4. DevOps: Finalize Docker setup, write docker-compose up instructions
5. **Gate:** Full application working in Docker, all tests passing, security review complete

### Phase 2: Hardening & Features (Complete)

- Celery + Redis for async PDF generation
- Admin panel (FastAPI web UI with Jinja2 templates)
- ATM cash cassette simulation
- Rate limiting and request throttling
- Structured logging (JSON) with correlation IDs
- Health check endpoints (`/health`, `/ready`)

### Phase 3: Cloud Deployment (Complete)

- Terraform IaC for AWS infrastructure (VPC, ECS Fargate, RDS PostgreSQL, S3 for statements)
- CI/CD pipeline: GitHub Actions → build Docker image → push to ECR → deploy to ECS
- Environment management (dev, staging, production)
- Monitoring: CloudWatch metrics and alarms
- Secrets management: AWS Secrets Manager for DB credentials, encryption keys

### Phase 4: Web UI (v2.0)

**Goal:** Add a skeuomorphic, interactive ATM web interface using React so users can experience the simulator in their browser. Desktop + tablet only (fixed aspect ratio, CSS scale-down).

**Design decisions:**
- **Framework:** React 18 + Vite + TypeScript (strict) — chosen for best animation ecosystem and instant transitions
- **Animations:** Framer Motion — spring physics, AnimatePresence, staggered sequences
- **State management:** useReducer state machine (17 screens, no React Router — ATMs don't have URL bars)
- **Deployment:** Single Docker container (multi-stage build: Node.js builds React → FastAPI serves static files)
- **API integration:** Axios with interceptors for X-Session-ID headers, 401 session expiry, 503 maintenance mode

**Sprint 1 — Foundation (project setup, ATM housing, first 2 screens)**
1. Initialize `frontend/` (Vite + React + TS + ESLint + Vitest)
2. Build ATM housing components (ATMFrame, ScreenBezel, SideButtons, NumericKeypad, CardSlot, CashDispenser, ReceiptPrinter)
3. Build state machine (ATMContext + atmReducer with 17 screens, 16 action types)
4. Build Axios API client with session header + 401/503 interceptors
5. Build WelcomeScreen + PinEntryScreen (with login API integration)
6. Backend: CORS middleware (dev), StaticFiles mount, SPA catch-all, `/session/refresh` endpoint
7. Add frontend CI jobs (lint, test, build) to GitHub Actions
8. Write Vitest tests (100+ tests, 99%+ statement coverage)
9. **Gate:** Card insert → PIN entry → auth success/failure works. ATM housing visually complete. All tests pass. CI green.

**Sprint 2 — Core Transaction Screens (all 17 screens, API integration)**
1. Build all remaining screens: MainMenu, BalanceInquiry, Withdrawal (3 screens), Deposit (2), Transfer (3), Statement, PinChange, SessionTimeout, Error, Maintenance
2. Build `useIdleTimer` hook for session timeout with 30s warning overlay
3. Backend: `GET /statements/download/{filename}` endpoint
4. Write typed API endpoint functions for all operations
5. Vitest tests for all screens + MSW API integration tests (65-80 new tests)
6. **Gate:** All 17 screens functional. Every API endpoint called correctly. Session timeout works. 90+ frontend tests pass.

**Sprint 3 — Animations + Polish + Browser Testing**
1. Card insertion, cash dispensing, receipt printing animations (Framer Motion)
2. Screen transition animations (AnimatePresence)
3. Keypad + side button press feedback
4. Loading spinner overlay, session timeout warning overlay
5. ATM typography (monospace/LCD font), CRT glow effect, responsive scaling
6. Playwright browser E2E tests (18-22 tests)
7. **Gate:** All animations smooth (60fps). Playwright E2E passes. Feels like a real ATM.

**Sprint 4 — Docker, Documentation, Final Polish**
1. Update Dockerfile with Node.js build stage (multi-stage)
2. Update CLAUDE.md, README.md, docs/architecture.md
3. Write docs/frontend-architecture.md
4. Full smoke test: `docker-compose up` → browser → all flows
5. Stability run: test suite 5x for flakiness report
6. **Gate:** All CI jobs green. `docker-compose up` serves complete ATM UI. Documentation complete.

### Sprint Checkpoint Protocol

At the end of every sprint, after all tests pass and code is committed/pushed:

1. **Git tag** — `git tag v2.0-sprint{N}` + `git push --tags` (clean restore point)
2. **CI verification** — confirm all CI jobs are green on the tagged commit
3. **Context compact** — start a fresh conversation for the next sprint with a summary of completed work and next sprint scope

This ensures we have a rollback point at every sprint gate and avoid context limit issues.

---

## Quality Standards

### Code Quality

- **Type hints on every function signature.** No `Any` types except where unavoidable (and must be commented with justification).
- **Docstrings on all public functions and classes.** Google-style format. Include `Args`, `Returns`, `Raises` sections.
- **Ruff** for linting and formatting (line length: 100).
- **mypy strict mode** must pass with zero errors.
- All monetary amounts stored as `Decimal` (never `float`). Use integer cents internally for all calculations to avoid floating-point rounding issues. Convert to dollar display format only at the presentation layer.
- **No magic numbers.** All business rules (limits, timeouts, thresholds) must be defined as named constants or configuration values, never hardcoded inline.
- **Single Responsibility Principle.** Each function does one thing. If a function exceeds 40 lines, it should be decomposed.
- **Explicit error handling.** No bare `except:` clauses. All exceptions must be specific, logged, and result in meaningful user-facing error messages.

### Frontend Code Quality

- **TypeScript strict mode** (`strict: true`, `noUnusedLocals`, `noUncheckedIndexedAccess`). Zero errors required.
- **ESLint** with `--max-warnings=0`. No warnings allowed.
- **React-specific rules:** `eslint-plugin-react-hooks` (recommended) + `eslint-plugin-react-refresh`.
- **Component architecture:** Presentational components receive data via props. State machine logic lives exclusively in `atmReducer.ts`. Screens dispatch actions; they do not call APIs directly except during login flow.
- **CSS approach:** Plain CSS with custom properties (CSS variables). Metallic gradients and CRT glow effects via CSS. No CSS-in-JS libraries.
- **Animation rules:** Only `transform` and `opacity` properties (GPU-composited). `prefers-reduced-motion` media query disables all animations. No layout-triggering animations.
- **Accessibility:** All interactive elements have `aria-label`. Keyboard navigation via physical key mapping (0-9, Enter, Escape, Backspace).

---

### Testing Strategy

#### Python Coverage Targets

| Code Category | Coverage Target | Rationale |
|---|---|---|
| `services/` (business logic) | **100%** | Financial transaction logic — every branch must be verified. A missed code path here is a potential monetary error. |
| `utils/security.py` | **100%** | PIN hashing, input sanitization, masking — security code must have zero untested paths. |
| `utils/formatting.py` | **100%** | Currency formatting, account masking — display errors erode user trust. |
| `models/` (model methods, validators, properties) | **100%** | Data integrity validators and computed properties must be fully exercised. |
| `schemas/` (custom validators) | **100%** | Input validation is a security boundary. Every validation rule must be tested for acceptance and rejection. |
| `api/` (route handlers) | **95%+** | Covered primarily through integration tests. Minor gaps acceptable for framework-generated error handlers. |
| `pdf/` (statement generation) | **95%+** | Core generation logic at 100%; minor formatting edge cases may be impractical to cover. |
| `ui/` (Textual screens) | **90%+** | UI wiring and event handlers tested; some visual rendering paths are framework-internal. |
| `db/`, `config.py`, `main.py` | **90%+** | Infrastructure glue code. Tested through integration tests; trivial boilerplate may be excluded with documented justification. |
| **Overall project** | **95%+** | Measured via `pytest-cov`. Any file below 90% requires a written justification in the PR description. |

#### Frontend Coverage Targets

| Code Category | Coverage Target | Rationale |
|---|---|---|
| `state/` (reducer, types) | **100%** | State machine is the backbone — every branch must be verified. |
| `api/` (client, endpoints) | **95%+** | Network layer; interceptors are critical for session management. |
| `hooks/` | **100%** | Shared logic consumed by multiple components. |
| `components/screens/` | **90%+ statements** | User-facing screens; some animation internals hard to unit test. |
| `components/atm-housing/` | **90%+** | Structural components; visual details covered by E2E. |
| **Overall frontend** | **90%+ statements, 85%+ branches** | Measured via `@vitest/coverage-v8`. |

> **Note on v8 function coverage:** v8 counts each `useCallback`, arrow function, and inline handler inside React components as a separate function entry, inflating the denominator. **Lines and statements are the primary quality gate** for React code. The function threshold is set to 65% to account for this v8 behavior.

Coverage thresholds are enforced in `vite.config.ts` and fail the `npm run test:coverage` command if not met. The `frontend-test` CI job enforces these thresholds on every PR.

> **Exclusion policy:** Lines excluded from coverage (via `# pragma: no cover`) must include an inline comment explaining why. Additionally, the SDET must log every exclusion in `tests/COVERAGE_EXCLUSIONS.md` with the file path, line number(s), reason, and date added. This file is reviewed by the Team Lead before any sprint gate. Acceptable exclusion reasons: defensive error handling for conditions that cannot be triggered in tests (e.g., database connection failures during migration), abstract base class methods that exist only for interface contracts, or platform-specific branches that cannot execute in the test environment. **"It's hard to test" is never an acceptable reason.** If something is hard to test, that's a design problem — refactor the code to make it testable.

#### Unit Tests

Every public function in the `services/`, `utils/`, and `schemas/` packages must have dedicated unit tests covering:

1. **Happy path** — expected inputs produce expected outputs
2. **Boundary values** — zero amounts, exact-limit amounts, one-cent-over-limit amounts, maximum values
3. **Invalid inputs** — wrong types, negative amounts, empty strings, None values, SQL injection attempts
4. **State transitions** — account lockout after N failures, daily limit resets, hold expiration

**Financial calculation tests must use exact `Decimal` assertions, not approximate comparisons.**

#### Integration Tests

Every API endpoint must have integration tests covering:

| Endpoint Category | Required Test Scenarios |
|---|---|
| **Auth endpoints** | Valid login, invalid PIN, expired session, locked account, concurrent session attempt |
| **Withdrawal endpoints** | Successful withdrawal, insufficient funds, exceeds daily limit, invalid amount (not multiple of 20), zero amount, negative amount, account frozen |
| **Deposit endpoints** | Cash deposit (immediate availability), check deposit (hold applied), zero amount, deposit to closed account |
| **Transfer endpoints** | Own-account transfer, external transfer, insufficient funds, exceeds daily limit, transfer to nonexistent account, transfer to self (same account), zero amount |
| **Statement endpoints** | Valid date range, empty date range (no transactions), invalid date range (future dates, end before start), PDF generation and content verification |
| **PIN management** | Successful change, incorrect current PIN, new PIN fails complexity rules, new PIN matches old PIN |

Integration tests must verify: HTTP status codes, response body structure (Pydantic schema compliance), database state changes (balance updates, transaction records created), and audit log entries generated.

#### End-to-End (E2E) Tests

E2E tests simulate complete user journeys through the application, exercising authentication, business logic, database persistence, and response formatting as an integrated system. Each test is independent and leaves no side effects for other tests.

**Authentication Journeys (6 tests)**

| # | Test Name | Scenario | Expected Outcome |
|---|---|---|---|
| E2E-AUTH-01 | Successful Login | Enter valid card number + correct PIN | Session created, main menu displayed, audit log records successful auth |
| E2E-AUTH-02 | Wrong PIN Single Attempt | Enter valid card number + incorrect PIN | Error message displayed, failed_attempts incremented to 1, user may retry |
| E2E-AUTH-03 | Account Lockout | Enter incorrect PIN 3 consecutive times | Account locked, lockout message with remaining duration displayed, audit log records lockout event |
| E2E-AUTH-04 | Login to Locked Account | Attempt login during active lockout period | Immediate rejection with time-remaining message, no PIN verification attempted |
| E2E-AUTH-05 | Session Timeout | Login successfully, wait beyond 2-minute timeout, attempt operation | Session expired message, user returned to login screen, audit log records timeout |
| E2E-AUTH-06 | Successful PIN Change | Login → navigate to PIN change → enter current PIN → enter new PIN → confirm → logout → login with new PIN | PIN updated in database (new hash), old PIN no longer works, new PIN authenticates successfully, audit log records PIN change |

**Withdrawal Journeys (8 tests)**

| # | Test Name | Scenario | Expected Outcome |
|---|---|---|---|
| E2E-WDR-01 | Quick Withdraw $100 | Login (Alice, checking $5,250) → select quick withdraw $100 | Balance reduced to $5,150, transaction record created, daily_withdrawal_used updated, receipt displayed with denomination breakdown |
| E2E-WDR-02 | Custom Amount Withdraw | Login (Alice) → enter custom amount $260 | Balance reduced by $260, amount validated as multiple of $20, transaction recorded |
| E2E-WDR-03 | Non-Standard Amount Rejected | Login → enter custom amount $55 | Error: amount must be multiple of $20, no balance change, no transaction created |
| E2E-WDR-04 | Insufficient Funds | Login (Bob, checking $850.75) → withdraw $900 | Error: insufficient funds, balance unchanged, no transaction created, audit log records declined transaction |
| E2E-WDR-05 | Daily Limit Enforcement | Login (Alice) → withdraw $200, then $200, then $200 (total $600, exceeding $500 limit) | First two succeed, third rejected with daily limit message, balance reflects only first two withdrawals |
| E2E-WDR-06 | Withdraw Exact Balance | Login (Bob, $850.75) → withdraw $840 (largest multiple of $20 ≤ balance) | Withdrawal succeeds, balance reduced to $10.75 |
| E2E-WDR-07 | Zero Balance Account | Login (Charlie, checking $0.00) → attempt any withdrawal | Error: insufficient funds, no transaction created |
| E2E-WDR-08 | Overdraft Protection Trigger | Login (Charlie, checking $0.00 with linked savings $100) → withdraw $60 with overdraft protection enabled | $60 transferred from savings to checking, then withdrawn. Savings reduced to $40, checking at $0, two transaction records created (transfer + withdrawal) |

**Deposit Journeys (5 tests)**

| # | Test Name | Scenario | Expected Outcome |
|---|---|---|---|
| E2E-DEP-01 | Cash Deposit Standard | Login (Bob) → cash deposit $500 | Balance increases by $500, available_balance increases by $200 immediately (remainder held 1 business day), deposit receipt generated with reference number |
| E2E-DEP-02 | Cash Deposit Small Amount | Login → cash deposit $150 (under $200 threshold) | Full $150 available immediately (no hold), balance and available_balance both increase by $150 |
| E2E-DEP-03 | Check Deposit | Login → check deposit $1,000 with check #4521 | Balance increases by $1,000, first $200 available next business day, remainder after 2 business days, hold_until dates set correctly on transaction, receipt includes check number |
| E2E-DEP-04 | Deposit to Savings | Login (Alice) → deposit $300 cash to savings account | Savings balance increases, same hold policy applies, correct account targeted |
| E2E-DEP-05 | Multiple Deposits Single Session | Login → cash deposit $200 → check deposit $500 | Both transactions recorded independently, balances and holds calculated correctly for each, running balance accurate |

**Transfer Journeys (7 tests)**

| # | Test Name | Scenario | Expected Outcome |
|---|---|---|---|
| E2E-TRF-01 | Own Account Transfer (Checking → Savings) | Login (Alice) → transfer $1,000 from checking to savings | Checking reduced to $4,250, savings increased to $13,500, two transaction records (TRANSFER_OUT + TRANSFER_IN), confirmation displayed |
| E2E-TRF-02 | Own Account Transfer (Savings → Checking) | Login (Alice) → transfer $500 from savings to checking | Savings reduced, checking increased, two transaction records created |
| E2E-TRF-03 | External Transfer | Login (Alice) → transfer $200 to Bob's account (1000-0002-0001) | Alice checking reduced by $200, Bob checking increased by $200, both accounts have transaction records, related_account_id populated on both |
| E2E-TRF-04 | Transfer Insufficient Funds | Login (Charlie, checking $0.00) → transfer $50 to Alice | Error: insufficient funds, no balances changed, no transaction records created |
| E2E-TRF-05 | Transfer Exceeds Daily Limit | Login (Alice) → transfer $2,000 then $1,000 (total $3,000, exceeding $2,500 limit) | First transfer succeeds, second rejected with daily limit message, only first transfer reflected in balances |
| E2E-TRF-06 | Transfer to Nonexistent Account | Login (Alice) → transfer $100 to account 9999-9999-9999 | Error: destination account not found, no balance changes, audit log records failed transfer attempt |
| E2E-TRF-07 | Transfer to Same Account | Login (Alice) → transfer from checking to same checking account | Error: cannot transfer to same account, no transaction created |

**Statement Journeys (5 tests)**

| # | Test Name | Scenario | Expected Outcome |
|---|---|---|---|
| E2E-STM-01 | 7-Day Statement Generation | Login (Alice) → request 7-day statement after several transactions | PDF generated, contains: account holder name, masked account number, opening balance, all transactions within 7 days with dates and descriptions, running balance per transaction, closing balance, summary totals |
| E2E-STM-02 | 30-Day Statement | Login → request 30-day statement | PDF generated with full 30-day transaction history, correct opening/closing balances |
| E2E-STM-03 | Custom Date Range | Login → request statement from specific start date to end date | Only transactions within range included, opening balance reflects pre-range state |
| E2E-STM-04 | Empty Statement | Login (Charlie) → request statement for period with no transactions | PDF generated with zero transactions, opening and closing balance both $0.00, no errors |
| E2E-STM-05 | Statement After Mixed Operations | Login (Alice) → withdraw $100 → deposit $500 → transfer $200 → request statement | All three transaction types appear in correct chronological order, running balance accurate after each, final balance matches account balance |

**Balance Inquiry Journeys (3 tests)**

| # | Test Name | Scenario | Expected Outcome |
|---|---|---|---|
| E2E-BAL-01 | Standard Balance Check | Login (Alice) → check balance | Displays available balance and total balance, shows last 5 transactions as mini-statement |
| E2E-BAL-02 | Balance With Active Holds | After a check deposit with hold → check balance | available_balance reflects hold (less than total balance), hold details visible |
| E2E-BAL-03 | Balance After Operations | Login → withdraw $100 → check balance | Balance reflects withdrawal, withdrawal appears in last-5-transactions mini-statement |

**Cross-Feature Compound Journeys (4 tests)**

| # | Test Name | Scenario | Expected Outcome |
|---|---|---|---|
| E2E-CMP-01 | Full Session Lifecycle | Login → check balance → withdraw $100 → transfer $50 to savings → request statement → logout | All operations succeed sequentially, each operation's effect visible in subsequent operations, statement includes all session transactions, session cleanly terminated |
| E2E-CMP-02 | Deposit Availability Progression | Deposit $500 cash → verify available_balance ($200 immediate) → simulate hold expiration → verify full $500 available | Hold policy correctly gates availability, balance transitions correctly after hold clears |
| E2E-CMP-03 | Daily Limit Reset | Withdraw $400 (approaching $500 limit) → verify $100 remaining daily allowance → simulate day rollover → verify full $500 limit restored | Daily limits track correctly within a day and reset on new day boundary |
| E2E-CMP-04 | Multi-Account Customer Journey | Login (Alice) → check checking balance → check savings balance → transfer $500 checking→savings → withdraw $200 from checking → generate statement for each account | Cross-account operations consistent, both account statements reflect shared transfer, no double-counting |

**Error Handling & Edge Case Journeys (4 tests)**

| # | Test Name | Scenario | Expected Outcome |
|---|---|---|---|
| E2E-ERR-01 | Frozen Account Operations | Admin freezes Bob's account → Bob logs in → attempts withdrawal | Authentication may succeed but all operations rejected with "account frozen" message |
| E2E-ERR-02 | Concurrent Transaction Safety | Two simultaneous withdrawal requests on same account totaling more than balance | Exactly one succeeds, one fails with insufficient funds (no negative balance possible), database remains consistent |
| E2E-ERR-03 | Negative Amount Injection | Attempt withdrawal of -$100, transfer of -$50, deposit of -$200 via API | All rejected at validation layer (Pydantic schema), no transactions created, no balance changes, audit log records validation failures |
| E2E-ERR-04 | Maximum Value Boundaries | Deposit $999,999,999.99, transfer $999,999,999.99 | System handles large values without overflow, Decimal precision maintained, appropriate limit enforcement applied |

**Total E2E Test Count: 42 tests across 8 categories**

#### Test Execution & Reporting

- **All tests run in CI** on every pull request via GitHub Actions
- **E2E tests use a dedicated test database** seeded fresh before each test (no shared state between tests)
- **Test execution order is randomized** (`pytest-randomly`) to catch hidden dependencies
- **Coverage reports generated as CI artifacts** and posted as PR comments
- **Failing tests block merge.** No exceptions. If a test is flaky, fix the test or fix the code — do not skip it.
- **Performance baseline:** E2E test suite must complete within 120 seconds. Tests exceeding 5 seconds individually must be flagged for optimization.

#### Test File Organization

```
tests/
├── conftest.py                    # Shared fixtures: test DB, async client, seed data factory
├── factories.py                   # Factory functions for test data (customers, accounts, cards)
├── COVERAGE_EXCLUSIONS.md         # Centralized log of all pragma: no cover exclusions with justifications
├── unit/
│   ├── services/
│   │   ├── test_auth_service.py
│   │   ├── test_transaction_service.py
│   │   ├── test_account_service.py
│   │   ├── test_statement_service.py
│   │   └── test_audit_service.py
│   ├── utils/
│   │   ├── test_security.py
│   │   └── test_formatting.py
│   ├── schemas/
│   │   ├── test_auth_schemas.py
│   │   ├── test_account_schemas.py
│   │   └── test_transaction_schemas.py
│   └── models/
│       ├── test_customer_model.py
│       ├── test_account_model.py
│       ├── test_transaction_model.py
│       └── test_card_model.py
├── integration/
│   ├── test_auth_api.py
│   ├── test_withdrawal_api.py
│   ├── test_deposit_api.py
│   ├── test_transfer_api.py
│   ├── test_statement_api.py
│   ├── test_balance_api.py
│   └── test_pin_management_api.py
└── e2e/
    ├── test_auth_journeys.py       # E2E-AUTH-01 through E2E-AUTH-06
    ├── test_withdrawal_journeys.py # E2E-WDR-01 through E2E-WDR-08
    ├── test_deposit_journeys.py    # E2E-DEP-01 through E2E-DEP-05
    ├── test_transfer_journeys.py   # E2E-TRF-01 through E2E-TRF-07
    ├── test_statement_journeys.py  # E2E-STM-01 through E2E-STM-05
    ├── test_balance_journeys.py    # E2E-BAL-01 through E2E-BAL-03
    ├── test_compound_journeys.py   # E2E-CMP-01 through E2E-CMP-04
    └── test_error_journeys.py      # E2E-ERR-01 through E2E-ERR-04
```

#### Frontend Test Execution

- **Both test suites must pass independently before any commit/push:**
  - `pytest --cov=src/atm` — Python backend (562+ tests)
  - `npx vitest run --coverage` — React frontend (109+ tests, growing)
- **CI runs both suites in parallel** — 5 Python jobs + 3 frontend jobs (8 total)
- **Failing tests in either suite block merge.** No exceptions.
- **Frontend tests use jsdom** for component/hook tests and **Playwright** for browser E2E tests.
- **MSW (Mock Service Worker)** mocks API responses in frontend integration tests — no dependency on a running backend.

#### Frontend Test File Organization

```
frontend/src/__tests__/
├── setup.ts                       # @testing-library/jest-dom setup
├── state/
│   └── atmReducer.test.ts         # All 16 action types + edge cases
├── api/
│   ├── client.test.ts             # Axios interceptors (session header, 401, 503)
│   └── endpoints.test.ts          # All API endpoint functions (mocked client)
├── hooks/
│   └── useATMContext.test.tsx      # Context hook + error boundary
├── components/
│   ├── ATMHousing.test.tsx         # ATMFrame, ScreenBezel, CardSlot, CashDispenser, ReceiptPrinter
│   ├── SideButtons.test.tsx        # Side button rendering + click handlers
│   ├── NumericKeypad.test.tsx      # All buttons + physical keyboard mapping
│   ├── WelcomeScreen.test.tsx      # Card number input + validation
│   ├── PinEntryScreen.test.tsx     # PIN entry + keypad handlers + API calls
│   ├── screens.test.tsx            # ErrorScreen, SessionTimeout, Maintenance, MainMenu
│   └── App.test.tsx                # Full app render + screen transitions + side buttons
└── e2e/                            # (Sprint 3) Playwright browser tests
```

### Security

- PINs stored as bcrypt hashes with application-level pepper, never plaintext, **never logged — not even masked**
- Account numbers masked in all user-facing output (show last 4 digits only)
- All inputs validated via Pydantic schemas before reaching business logic — **the API layer trusts nothing**
- SQL injection prevention via SQLAlchemy parameterized queries (no raw SQL anywhere in the codebase)
- Audit log captures: all authentication attempts (success and failure), all transactions (success and failure), all admin actions, all session lifecycle events
- Session tokens are cryptographically random (via `secrets.token_urlsafe`), opaque, and expire after 2 minutes of inactivity
- **Rate limiting:** Maximum 5 authentication attempts per card number per 15-minute window (in addition to the 3-attempt lockout per session)
- **No sensitive data in error messages.** Error responses must never reveal whether a card number exists — use generic "authentication failed" for both invalid card and invalid PIN.
- **Dependency scanning:** `pip-audit` (Python) and `npm audit` (frontend) run in CI to flag known vulnerabilities
- **SAST scanning:** Bandit scans all Python source code for security anti-patterns (hardcoded passwords, `eval()`, weak crypto, insecure deserialization)
- **Container/IaC scanning:** Trivy scans the filesystem for dependency CVEs and Terraform misconfigurations (CRITICAL/HIGH only)
- **Secret detection:** Gitleaks scans full git history for leaked API keys, tokens, passwords, and private keys
- **Automated dependency updates:** Dependabot opens weekly PRs for vulnerable pip, npm, and GitHub Actions dependencies

- **CodeQL Analysis:** `.github/workflows/codeql.yml` runs deep SAST (SQL injection, XSS, taint tracking) for both Python and TypeScript on every push/PR and weekly. Free for public repos; requires GitHub Advanced Security for private repos.

> **Public Repo Checklist:** After making the repository public, enable these free GitHub-native features in **Settings > Code security and analysis**:
> - **GitHub Secret Scanning** — Detects leaked API keys/tokens in pushed code.
> - **Secret Push Protection** — Blocks pushes containing secrets before they reach the repository.
> - **Dependabot Security Alerts** — Automatic CVE notifications for vulnerable dependencies.

### Git Conventions

- Branch naming: `feature/`, `bugfix/`, `hotfix/` prefixes
- Commit messages: conventional commits format (`feat:`, `fix:`, `test:`, `docs:`, `chore:`)
- Every feature branch must have passing CI before merge
- **PR requirements:** At minimum, the Team Lead must review all PRs. PRs touching `services/` or `utils/security.py` also require Security Engineer review.
- **No force-pushes to `main`.** Branch protection rules enforced.
- **All security scans must pass before merge.** Bandit, pip-audit, npm audit, Trivy, and Gitleaks are CI-blocking.

---

## Seed Data

The database seeder (`scripts/seed_db.py`) should create the following test accounts:

| Customer | Account | Type | Balance | PIN |
|---|---|---|---|---|
| Alice Johnson | 1000-0001-0001 | Checking | $5,250.00 | 1234 |
| Alice Johnson | 1000-0001-0002 | Savings | $12,500.00 | 1234 |
| Bob Williams | 1000-0002-0001 | Checking | $850.75 | 5678 |
| Charlie Davis | 1000-0003-0001 | Checking | $0.00 | 9012 |
| Charlie Davis | 1000-0003-0002 | Savings | $100.00 | 9012 |

This gives us test scenarios for: multi-account customers, low-balance edge cases, zero-balance accounts, and cross-account transfers.

---

## How to Launch the Agent Team

### Prerequisites
- Claude Code installed with Claude Max subscription
- Agent Teams enabled: add `"env": {"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"}` to your `~/.claude/settings.json`

### Recommended Launch Prompt

Open Claude Code in the project root directory and use a prompt like this:

```
I need you to act as Team Lead for building a Python ATM simulator application.
Read CLAUDE.md thoroughly — it contains the full project specification, team structure,
and development phases.

Create an agent team with these teammates:
1. Architect — system design, data models, API contracts
2. Backend Engineer — core Python/FastAPI implementation  
3. UX Designer — Textual terminal UI
4. SDET — testing strategy and test implementation
5. Security Engineer — auth, encryption, audit, threat model
6. DevOps Engineer — Docker, CI/CD, deployment config

Start with Phase 1, Sprint 1. Use delegate mode — coordinate only, do not implement.
Require plan approval from all agents before they begin implementation.
Assign clear file ownership per CLAUDE.md to avoid conflicts.
```

### Tips for Running the Team

1. **Use delegate mode** (`Shift+Tab`) so the lead coordinates rather than coding.
2. **Start with Sprint 1 only.** Let the Architect and DevOps agents finish design documents before spawning implementation agents. This prevents rework.
3. **Monitor file conflicts.** If two agents need to touch the same file, create a task dependency so they work sequentially.
4. **Keep the lead focused.** If the lead starts going off-track, message it: "Focus on coordination. Check task progress and unblock agents."
5. **Budget for tokens.** Agent teams use roughly 5-7x the tokens of a single session. With 6 teammates, this is a heavy workload — Max 20x ($200/mo) is recommended for sustained multi-agent development.

---

## Environment Variables

```env
# .env.example
DATABASE_URL=postgresql+asyncpg://atm_user:atm_pass@db:5432/atm_db
DATABASE_URL_SYNC=postgresql://atm_user:atm_pass@db:5432/atm_db
SECRET_KEY=change-me-in-production
PIN_PEPPER=change-me-in-production
SESSION_TIMEOUT_SECONDS=120
MAX_FAILED_PIN_ATTEMPTS=3
LOCKOUT_DURATION_SECONDS=1800
DAILY_WITHDRAWAL_LIMIT=50000  # in cents
DAILY_TRANSFER_LIMIT=250000   # in cents
STATEMENT_OUTPUT_DIR=/app/statements
LOG_LEVEL=INFO
ENVIRONMENT=development
FRONTEND_ENABLED=true           # Set to false to disable static file serving
```

---

## References & Useful Links

### Backend
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Tutorial](https://docs.sqlalchemy.org/en/20/tutorial/)
- [Textual Documentation](https://textual.textualize.io/)
- [ReportLab User Guide](https://docs.reportlab.com/reportlab/userguide/)

### Frontend (v2.0)
- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vite.dev/)
- [Framer Motion Documentation](https://motion.dev/)
- [Vitest Documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [Playwright Documentation](https://playwright.dev/)

### Infrastructure
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Terraform Documentation](https://developer.hashicorp.com/terraform)
- [Claude Code Agent Teams](https://code.claude.com/docs/en/agent-teams)
- [Conventional Commits](https://www.conventionalcommits.org/)
