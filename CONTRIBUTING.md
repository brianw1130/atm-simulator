# Contributing to ATM Simulator

Thank you for your interest in contributing! This guide will help you get started.

## Reporting Bugs

Open a [GitHub Issue](https://github.com/brianw1130/atm-simulator/issues/new) with:

- A clear title describing the problem
- Steps to reproduce the issue
- Expected behavior vs. actual behavior
- Your environment (OS, Docker version, Python version)

## Submitting Pull Requests

1. Fork the repository and create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following the code style guidelines below.

3. Run the full test suite and ensure everything passes:
   ```bash
   # Python tests
   pytest --cov=src/atm --cov-report=term-missing

   # Frontend tests
   cd frontend && npx vitest run --coverage

   # Linting and type checking
   ruff check . && ruff format --check .
   mypy --strict src/
   cd frontend && npx eslint . --max-warnings=0 && npx tsc --noEmit
   ```

4. Commit using [Conventional Commits](https://www.conventionalcommits.org/) format:
   ```
   feat: add new withdrawal denomination
   fix: correct daily limit calculation
   test: add edge case for zero-balance transfer
   docs: update API reference for deposit endpoint
   ```

5. Open a pull request against `main` with a clear description of the changes.

## Code Style

**Python:**
- Type hints on every function signature (strict mypy)
- Ruff for linting and formatting (line length: 100)
- All monetary values as integer cents (never float)
- Google-style docstrings on public functions

**TypeScript:**
- Strict mode enabled (`strict: true`, `noUncheckedIndexedAccess`)
- ESLint with zero warnings allowed
- Plain CSS with custom properties (no CSS-in-JS)

## Development Setup

See the [README](README.md) for Docker and local setup instructions, or the [Deployment Guide](docs/deployment.md) for detailed environment configuration.

## Architecture

- [Architecture](docs/architecture.md) — Backend system design, ADRs, data model
- [Frontend Architecture](docs/frontend-architecture.md) — React state machine, components, animations
- [API Reference](docs/api.md) — Endpoint specifications

## Testing

- **Coverage targets:** 100% for services/utils/models/schemas, 95%+ for API routes, 90%+ for UI
- **All tests must pass** before a PR can be merged — no exceptions
- **No skipped or flaky tests** — if a test is unreliable, fix the test or the code
- See `tests/COVERAGE_EXCLUSIONS.md` for documented exclusions with justifications
