# Load / Performance Tests

Load tests for the ATM Simulator API using [Locust](https://locust.io/).

## Prerequisites

- The ATM API server must be running (locally or in Docker)
- Test accounts must be seeded in the database
- Install dev dependencies: `pip install -e ".[dev]"`

## Running Load Tests

### Headless Mode (CI-friendly)

```bash
# 100 concurrent users, 10 spawned per second, run for 60 seconds
locust -f tests/load/locustfile.py --headless \
    -u 100 -r 10 -t 60s \
    --host http://localhost:8000
```

### Web UI Mode

```bash
locust -f tests/load/locustfile.py --host http://localhost:8000
# Open http://localhost:8089 in your browser
```

## Test Scenarios

| Scenario | Weight | Description |
|----------|--------|-------------|
| AuthFlowUser | 3 | Login, balance check, logout cycle |
| WithdrawalFlowUser | 2 | Login and repeated $100 withdrawals |
| DepositFlowUser | 2 | Login and repeated $200 cash deposits |
| TransferFlowUser | 1 | Login and $50 checking-to-savings transfers |
| HealthCheckUser | 1 | /health and /ready endpoint baseline |

Weights control the relative proportion of each user type.

## Performance Baseline

Per CLAUDE.md, the E2E test suite must complete within 120 seconds, and individual
tests exceeding 5 seconds must be flagged. Use the Locust results to identify
endpoints with P95 response times exceeding 500ms under load.
