# Deployment Guide

> **Owner:** DevOps / Cloud Engineer

## Prerequisites

Before setting up the ATM Simulator, ensure the following tools are installed:

| Tool | Minimum Version | Purpose |
|---|---|---|
| **Docker** | 24.0+ | Container runtime for the application and database |
| **Docker Compose** | v2.20+ | Multi-container orchestration (included with Docker Desktop) |
| **Python** | 3.12+ | Required only for local development without Docker |
| **Git** | 2.x | Clone the repository |

Verify your installations:

```bash
docker --version
docker compose version
python3 --version
git --version
```

## Quick Start with Docker

The fastest way to get the application running is with Docker Compose, which starts both the application and a PostgreSQL database.

```bash
# 1. Clone the repository
git clone <repo-url> && cd atm-simulator

# 2. Create environment file from template
cp .env.example .env

# 3. Build and start all services (app + PostgreSQL)
docker compose up --build

# 4. In a separate terminal, run database migrations
docker compose exec app alembic upgrade head

# 5. Seed the database with sample accounts
docker compose exec app python -m scripts.seed_db
```

The application will be available at `http://localhost:8000`. API docs are served at `http://localhost:8000/docs`.

To stop the services:

```bash
docker compose down          # stop containers, keep data
docker compose down -v       # stop containers and delete volumes (resets database)
```

## Local Development Without Docker

For local development, you can run the application directly using SQLite instead of PostgreSQL. This requires no external database setup.

```bash
# 1. Create and activate a virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# 2. Install the package with development dependencies
pip install -e ".[dev]"

# 3. Set environment variables for SQLite
export DATABASE_URL="sqlite+aiosqlite:///./atm.db"
export DATABASE_URL_SYNC="sqlite:///./atm.db"
export SECRET_KEY="local-dev-secret"
export PIN_PEPPER="local-dev-pepper"
export ENVIRONMENT="development"
export STATEMENT_OUTPUT_DIR="./statements"

# 4. Run database migrations
alembic upgrade head

# 5. Seed the database
python -m scripts.seed_db

# 6. Start the development server
uvicorn src.atm.main:app --reload --port 8000
```

### Running Tests Locally

```bash
# Run full test suite with coverage
pytest --cov=src/atm --cov-report=term-missing

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run only E2E tests
pytest tests/e2e/

# Run a specific test file
pytest tests/unit/services/test_auth_service.py -v
```

## Environment Variables

All configuration is managed through environment variables. Copy `.env.example` to `.env` and adjust as needed.

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://atm_user:atm_pass@db:5432/atm_db` | Async database connection string used by the SQLAlchemy async engine (asyncpg driver) |
| `DATABASE_URL_SYNC` | `postgresql://atm_user:atm_pass@db:5432/atm_db` | Synchronous connection string used by Alembic migrations |
| `SECRET_KEY` | `change-me-in-production` | Key for session token signing. **Must** be changed in production. |
| `PIN_PEPPER` | `change-me-in-production` | Application-level pepper appended to PINs before bcrypt hashing. **Must** be changed in production. |
| `SESSION_TIMEOUT_SECONDS` | `120` | Seconds of inactivity before a session expires (2 minutes) |
| `MAX_FAILED_PIN_ATTEMPTS` | `3` | Consecutive failed PIN entries before account lockout |
| `LOCKOUT_DURATION_SECONDS` | `1800` | Duration in seconds that an account stays locked after max failed attempts (30 minutes) |
| `DAILY_WITHDRAWAL_LIMIT` | `50000` | Daily withdrawal limit per account in cents ($500.00) |
| `DAILY_TRANSFER_LIMIT` | `250000` | Daily transfer limit per account in cents ($2,500.00) |
| `STATEMENT_OUTPUT_DIR` | `/app/statements` | Directory where generated PDF statements are saved |
| `LOG_LEVEL` | `INFO` | Python log level: DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `ENVIRONMENT` | `development` | Application environment: `development`, `testing`, or `production`. Controls debug features, docs endpoints, and database echo. |

## Database Setup

### Migrations (Alembic)

The project uses Alembic for database schema migrations.

```bash
# Apply all pending migrations
docker compose exec app alembic upgrade head

# Generate a new migration after model changes
docker compose exec app alembic revision --autogenerate -m "description of change"

# Roll back the most recent migration
docker compose exec app alembic downgrade -1

# View current migration status
docker compose exec app alembic current
```

### Seed Data

The seed script creates test accounts for local development:

```bash
docker compose exec app python -m scripts.seed_db
```

This creates five accounts across three customers (Alice, Bob, Charlie) with predefined balances and PINs. See `CLAUDE.md` for the full seed data table.

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration. The workflow is defined in `.github/workflows/ci.yml` and runs on every push to `main` and on every pull request targeting `main`.

### Jobs

All three jobs run in parallel on Ubuntu with Python 3.12 and pip caching enabled.

| Job | What It Does |
|---|---|
| **lint** | Installs dependencies, then runs `ruff check .` (linting) and `ruff format --check .` (formatting verification). Catches style violations and import ordering issues. |
| **type-check** | Runs `mypy --strict src/` to enforce type annotations across the entire source tree. All public functions must have complete type hints. |
| **test** | Runs `pytest` with coverage against a SQLite test database (no PostgreSQL required in CI). Generates both terminal and XML coverage reports. The XML report is uploaded as a build artifact. |

A failing job blocks pull request merges.

### Coverage Reports

After each test run, the coverage report is uploaded as a GitHub Actions artifact named `coverage-report`. Download it from the workflow run summary to inspect line-by-line coverage.

## Cloud Deployment (Phase 3)

Cloud deployment targets AWS and will be implemented in Phase 3. The planned architecture:

- **Compute:** ECS Fargate or App Runner for running the containerized application
- **Database:** Amazon RDS PostgreSQL for managed database hosting
- **Storage:** S3 for generated PDF statements
- **Secrets:** AWS Secrets Manager for credentials and encryption keys
- **CI/CD:** GitHub Actions builds and pushes Docker images to ECR, then deploys to ECS
- **Infrastructure as Code:** Terraform or AWS CDK for provisioning all resources
- **Environments:** Separate dev, staging, and production environments with isolated resources

Detailed deployment instructions will be added when Phase 3 implementation begins.
