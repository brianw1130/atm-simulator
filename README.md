# ATM Simulator

A full-featured Python ATM (Automated Teller Machine) simulator that replicates real-world ATM functionality including PIN authentication, cash withdrawals, deposits, fund transfers, balance inquiries, and PDF statement generation.

Built with **FastAPI**, **SQLAlchemy 2.0**, **PostgreSQL**, and **Textual** (terminal UI).

## Features

- **PIN Authentication** — Card number + PIN login with lockout after 3 failed attempts
- **Cash Withdrawal** — Quick-withdraw presets and custom amounts (multiples of $20), daily limits
- **Cash & Check Deposits** — Hold policies simulating real bank availability schedules
- **Fund Transfers** — Between own accounts or to other customers, with daily limits
- **Balance Inquiry** — Available and total balance with mini-statement (last 5 transactions)
- **PDF Statements** — Generate account statements for configurable date ranges
- **PIN Management** — Secure PIN change with complexity validation
- **Audit Logging** — Every authentication attempt and transaction is logged
- **Overdraft Protection** — Optional linked-account coverage for insufficient funds

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

The API will be available at `http://localhost:8000`. Interactive API docs are at `http://localhost:8000/docs`.

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
# Install dependencies
pip install -e ".[dev]"

# Set up environment variables
cp .env.example .env
# Edit .env to point DATABASE_URL to your local PostgreSQL

# Run migrations
alembic upgrade head

# Seed the database
python -m scripts.seed_db

# Start the API server
uvicorn src.atm.main:app --reload

# Run tests
pytest
```

### Running Tests

```bash
# Full test suite with coverage
pytest --cov=src/atm --cov-report=term-missing --cov-report=html

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# E2E tests only
pytest tests/e2e/

# Type checking
mypy src/

# Linting
ruff check src/ tests/
ruff format --check src/ tests/
```

### Coverage Requirements

| Code Category | Target |
|---|---|
| `services/`, `utils/security.py`, `models/`, `schemas/` | **100%** |
| `api/`, `pdf/` | **95%+** |
| `ui/` | **90%+** |
| **Overall** | **95%+** |

See `tests/COVERAGE_EXCLUSIONS.md` for documented exclusions.

## Project Structure

```
atm-simulator/
├── src/atm/           # Application source code
│   ├── api/           # FastAPI route handlers
│   ├── models/        # SQLAlchemy ORM models
│   ├── schemas/       # Pydantic request/response schemas
│   ├── services/      # Business logic layer
│   ├── db/            # Database session and seeding
│   ├── ui/            # Textual terminal UI
│   ├── pdf/           # PDF statement generation
│   └── utils/         # Security, formatting utilities
├── tests/             # Test suite (unit, integration, e2e)
├── alembic/           # Database migrations
├── docs/              # Project documentation
├── scripts/           # Utility scripts
└── docker-compose.yml # Local development environment
```

## Documentation

- [Architecture](docs/architecture.md) — System design, data model, technology decisions
- [API Reference](docs/api.md) — Endpoint specifications and examples
- [Deployment Guide](docs/deployment.md) — Docker, CI/CD, and cloud deployment
- [User Guide](docs/user-guide.md) — How to use the ATM simulator

## Tech Stack

- **Python 3.12** / **FastAPI** / **SQLAlchemy 2.0** / **Alembic**
- **PostgreSQL 16** (production) / **SQLite** (testing)
- **Textual** (terminal UI) / **ReportLab** (PDF generation)
- **Docker** / **GitHub Actions** (CI/CD)
- **pytest** / **Ruff** / **mypy**

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
