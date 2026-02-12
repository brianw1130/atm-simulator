"""Locust load test scenarios for the ATM Simulator API.

Usage:
    # Start the API server first:
    docker-compose up -d
    # OR:
    uvicorn src.atm.main:app --port 8000

    # Run load test (headless):
    locust -f tests/load/locustfile.py --headless -u 100 -r 10 -t 60s \
        --host http://localhost:8000

    # Run with web UI:
    locust -f tests/load/locustfile.py --host http://localhost:8000
    # Then open http://localhost:8089

Scenarios:
    AuthFlowUser — Login, check balance, logout
    WithdrawalFlowUser — Login, withdraw $100, logout
    DepositFlowUser — Login, deposit $200, logout
    TransferFlowUser — Login, transfer $50, logout
    HealthCheckUser — Hit /health endpoint only (baseline)
"""

from locust import HttpUser, between, task

# Test accounts from seed data (CLAUDE.md).
# Each user class uses a different account to avoid lock contention.
ALICE = {"card_number": "1000-0001-0001", "pin": "1234"}
BOB = {"card_number": "1000-0002-0001", "pin": "5678"}
CHARLIE = {"card_number": "1000-0003-0001", "pin": "9012"}


class AuthFlowUser(HttpUser):
    """Simulates a user who logs in, checks balance, and logs out."""

    wait_time = between(1, 3)
    weight = 3  # Most common flow

    def on_start(self):
        """Login on start."""
        resp = self.client.post(
            "/api/v1/auth/login",
            json=ALICE,
            name="/api/v1/auth/login",
        )
        if resp.status_code == 200:
            self.session_id = resp.json().get("session_id")
        else:
            self.session_id = None

    @task(3)
    def check_balance(self):
        """Check account balance."""
        if not self.session_id:
            return
        self.client.get(
            "/api/v1/accounts/1/balance",
            headers={"X-Session-ID": self.session_id},
            name="/api/v1/accounts/{id}/balance",
        )

    @task(1)
    def logout_and_login(self):
        """Logout and re-login to simulate session cycling."""
        if self.session_id:
            self.client.post(
                "/api/v1/auth/logout",
                headers={"X-Session-ID": self.session_id},
                name="/api/v1/auth/logout",
            )
        resp = self.client.post(
            "/api/v1/auth/login",
            json=ALICE,
            name="/api/v1/auth/login",
        )
        if resp.status_code == 200:
            self.session_id = resp.json().get("session_id")
        else:
            self.session_id = None


class WithdrawalFlowUser(HttpUser):
    """Simulates a user who logs in and makes withdrawals."""

    wait_time = between(2, 5)
    weight = 2

    def on_start(self):
        """Login on start."""
        resp = self.client.post(
            "/api/v1/auth/login",
            json=ALICE,
            name="/api/v1/auth/login",
        )
        if resp.status_code == 200:
            self.session_id = resp.json().get("session_id")
        else:
            self.session_id = None

    @task
    def withdraw(self):
        """Withdraw $100."""
        if not self.session_id:
            return
        self.client.post(
            "/api/v1/transactions/withdraw",
            json={"amount_cents": 10000},
            headers={"X-Session-ID": self.session_id},
            name="/api/v1/transactions/withdraw",
        )


class DepositFlowUser(HttpUser):
    """Simulates a user who logs in and makes deposits."""

    wait_time = between(2, 5)
    weight = 2

    def on_start(self):
        """Login on start."""
        resp = self.client.post(
            "/api/v1/auth/login",
            json=BOB,
            name="/api/v1/auth/login",
        )
        if resp.status_code == 200:
            self.session_id = resp.json().get("session_id")
        else:
            self.session_id = None

    @task
    def deposit(self):
        """Deposit $200 cash."""
        if not self.session_id:
            return
        self.client.post(
            "/api/v1/transactions/deposit",
            json={"amount_cents": 20000, "deposit_type": "cash"},
            headers={"X-Session-ID": self.session_id},
            name="/api/v1/transactions/deposit",
        )


class TransferFlowUser(HttpUser):
    """Simulates a user who logs in and makes transfers."""

    wait_time = between(2, 5)
    weight = 1

    def on_start(self):
        """Login on start."""
        resp = self.client.post(
            "/api/v1/auth/login",
            json=ALICE,
            name="/api/v1/auth/login",
        )
        if resp.status_code == 200:
            self.session_id = resp.json().get("session_id")
        else:
            self.session_id = None

    @task
    def transfer(self):
        """Transfer $50 from checking to savings."""
        if not self.session_id:
            return
        self.client.post(
            "/api/v1/transactions/transfer",
            json={
                "destination_account_number": "1000-0001-0002",
                "amount_cents": 5000,
            },
            headers={"X-Session-ID": self.session_id},
            name="/api/v1/transactions/transfer",
        )


class HealthCheckUser(HttpUser):
    """Baseline user that only hits health endpoints."""

    wait_time = between(1, 2)
    weight = 1

    @task(3)
    def health(self):
        """Liveness check."""
        self.client.get("/health", name="/health")

    @task(1)
    def ready(self):
        """Readiness check."""
        self.client.get("/ready", name="/ready")
