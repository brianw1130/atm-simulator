# ATM Simulator

A full-featured Python ATM (Automated Teller Machine) simulator that replicates real-world ATM functionality including PIN authentication, cash withdrawals, deposits, fund transfers, balance inquiries, and PDF statement generation.

Built with **FastAPI**, **SQLAlchemy 2.0**, **PostgreSQL**, **React 18** (skeuomorphic web UI), and **Textual** (terminal UI).

## Features

- **Skeuomorphic Web UI** — Realistic ATM kiosk in the browser with metallic housing, CRT screen glow, animated card slot, cash dispenser, and receipt printer (React + Framer Motion)
- **PIN Authentication** — Card number + PIN login with lockout after 3 failed attempts
- **Cash Withdrawal** — Quick-withdraw presets and custom amounts (multiples of $20), daily limits
- **Cash & Check Deposits** — Hold policies simulating real bank availability schedules
- **Fund Transfers** — Between own accounts or to other customers, with daily limits
- **Balance Inquiry** — Available and total balance with mini-statement (last 5 transactions)
- **PDF Statements** — Generate account statements for configurable date ranges
- **PIN Management** — Secure PIN change with complexity validation
- **Session Timeout** — 2-minute idle timer with 30-second countdown warning
- **Audit Logging** — Every authentication attempt and transaction is logged
- **Admin Panel** — Account management, maintenance mode, audit log viewer

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)

### Run with Docker

```bash
# Clone the repository
git clone https://github.com/brianw1130/atm-simulator.git
cd atm-simulator

# Copy environment config
cp .env.example .env

# Build and start the application
docker compose up --build

# In a separate terminal, run database migrations and seed data
docker compose exec app alembic upgrade head
docker compose exec app python -m scripts.seed_db
```

**Web UI:** Open `http://localhost:8000` in your browser to use the ATM.

**API Docs:** Interactive Swagger docs at `http://localhost:8000/docs`.

**Development mode:** The Vite dev server runs at `http://localhost:5173` with hot module replacement.

### Run the Terminal UI

```bash
docker compose exec app python -m src.atm.ui.app
```

### Test Accounts

| Customer | Account Number | Type | Balance | PIN |
|---|---|---|---|---|
| Alice Johnson | 1000-0001-0001 | Checking | $5,250.00 | 1234 |
| Alice Johnson | 1000-0001-0002 | Savings | $12,500.00 | 1234 |
| Bob Williams | 1000-0002-0001 | Checking | $850.75 | 5678 |
| Charlie Davis | 1000-0003-0001 | Checking | $0.00 | 9012 |
| Charlie Davis | 1000-0003-0002 | Savings | $100.00 | 9012 |

## Development

### Local Setup (without Docker)

```bash
# Install Python dependencies
pip install -e ".[dev]"

# Set up environment variables
cp .env.example .env
# Edit .env to point DATABASE_URL to your local PostgreSQL

# Run migrations and seed data
alembic upgrade head
python -m scripts.seed_db

# Start the API server
uvicorn src.atm.main:app --reload

# In a separate terminal, start the frontend dev server
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Python test suite (582 tests)
pytest --cov=src/atm --cov-report=term-missing

# Frontend unit tests (223 tests)
cd frontend && npx vitest run --coverage

# Frontend browser E2E tests (36 tests)
cd frontend && npx playwright test

# Type checking
mypy src/
cd frontend && npx tsc --noEmit

# Linting
ruff check src/ tests/
ruff format --check src/ tests/
cd frontend && npx eslint . --max-warnings=0
```

### Coverage Requirements

| Code Category | Target |
|---|---|
| `services/`, `utils/security.py`, `models/`, `schemas/` | **100%** |
| `api/`, `pdf/` | **95%+** |
| `ui/` | **90%+** |
| Frontend (lines/statements) | **90%+** |
| **Overall (Python)** | **95%+** |

See `tests/COVERAGE_EXCLUSIONS.md` for documented exclusions.

## Project Structure

```
atm-simulator/
├── src/atm/              # Python backend
│   ├── api/              # FastAPI route handlers
│   ├── models/           # SQLAlchemy ORM models
│   ├── schemas/          # Pydantic request/response schemas
│   ├── services/         # Business logic layer
│   ├── db/               # Database session and seeding
│   ├── ui/               # Textual terminal UI
│   ├── pdf/              # PDF statement generation
│   └── utils/            # Security, formatting utilities
├── frontend/             # React web UI (v2.0)
│   ├── src/
│   │   ├── components/   # ATM housing + 17 screen components
│   │   ├── state/        # useReducer state machine (17 screens, 16 actions)
│   │   ├── api/          # Axios client + typed endpoint functions
│   │   ├── hooks/        # useATMContext, useIdleTimer
│   │   └── styles/       # CSS (metallic gradients, CRT glow, keypad)
│   └── __tests__/        # Vitest + Playwright tests
├── tests/                # Python test suite (unit, integration, e2e)
├── infra/                # Terraform IaC for AWS deployment
├── alembic/              # Database migrations
├── docs/                 # Project documentation
└── docker-compose.yml    # Local development environment
```

## Documentation

- [Architecture](docs/architecture.md) — System design, ADRs, data model, security threat model
- [Frontend Architecture](docs/frontend-architecture.md) — React state machine, component hierarchy, animation system
- [API Reference](docs/api.md) — Endpoint specifications and examples
- [Deployment Guide](docs/deployment.md) — Docker, CI/CD, and AWS cloud deployment
- [User Guide](docs/user-guide.md) — How to use the ATM simulator

## Tech Stack

**Backend:** Python 3.12 / FastAPI / SQLAlchemy 2.0 / Alembic / PostgreSQL 16 / Celery + Redis

**Frontend:** React 18 / TypeScript (strict) / Vite / Framer Motion / Axios

**Testing:** pytest (582 tests) / Vitest (223 tests) / Playwright (36 tests)

**Infrastructure:** Docker / GitHub Actions (11 CI jobs) / Terraform / AWS (ECS Fargate)

**Security:** Bandit / pip-audit / npm audit / Trivy / Gitleaks / Dependabot

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
