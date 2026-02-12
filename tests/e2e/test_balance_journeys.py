"""E2E tests for balance inquiry journeys.

E2E-BAL-01 through E2E-BAL-03 as specified in CLAUDE.md.
Each test is independent with fresh database state.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.e2e.conftest import seed_e2e_data


async def _login(client: AsyncClient, card_number: str, pin: str) -> str:
    """Helper: login and return the session ID."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"card_number": card_number, "pin": pin},
    )
    assert resp.status_code == 200
    return resp.json()["session_id"]


@pytest.mark.asyncio
async def test_e2e_bal_01_standard_balance_check(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """E2E-BAL-01: Standard Balance Check."""
    data = await seed_e2e_data(db_session)
    session_id = await _login(client, data["alice_card_number"], "7856")

    resp = await client.get(
        f"/api/v1/accounts/{data['alice_checking'].id}/balance",
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 200
    resp_data = resp.json()

    account = resp_data["account"]
    assert account["balance"] == "$5,250.00"
    assert account["available_balance"] == "$5,250.00"
    assert account["account_type"] == "CHECKING"
    assert account["status"] == "ACTIVE"

    assert "recent_transactions" in resp_data
    assert isinstance(resp_data["recent_transactions"], list)


@pytest.mark.asyncio
async def test_e2e_bal_02_balance_with_active_holds(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """E2E-BAL-02: Balance With Active Holds (check deposit)."""
    data = await seed_e2e_data(db_session)
    session_id = await _login(client, data["bob_card_number"], "5678")

    # Make a check deposit ($1,000, all held)
    dep_resp = await client.post(
        "/api/v1/transactions/deposit",
        json={
            "amount_cents": 100_000,
            "deposit_type": "check",
            "check_number": "5555",
        },
        headers={"X-Session-ID": session_id},
    )
    assert dep_resp.status_code == 201

    # Check balance
    bal_resp = await client.get(
        f"/api/v1/accounts/{data['bob_checking'].id}/balance",
        headers={"X-Session-ID": session_id},
    )

    assert bal_resp.status_code == 200
    bal_data = bal_resp.json()

    # Total: $850.75 + $1,000 = $1,850.75
    assert bal_data["account"]["balance"] == "$1,850.75"
    # Available: $850.75 (check fully held)
    assert bal_data["account"]["available_balance"] == "$850.75"

    # Check deposit in recent transactions
    assert len(bal_data["recent_transactions"]) >= 1
    recent_txn = bal_data["recent_transactions"][0]
    assert "Check Deposit" in recent_txn["description"]


@pytest.mark.asyncio
async def test_e2e_bal_03_balance_after_operations(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """E2E-BAL-03: Balance After Withdrawal."""
    data = await seed_e2e_data(db_session)
    session_id = await _login(client, data["alice_card_number"], "7856")

    # Withdraw $100
    w_resp = await client.post(
        "/api/v1/transactions/withdraw",
        json={"amount_cents": 10_000},
        headers={"X-Session-ID": session_id},
    )
    assert w_resp.status_code == 201

    # Check balance
    bal_resp = await client.get(
        f"/api/v1/accounts/{data['alice_checking'].id}/balance",
        headers={"X-Session-ID": session_id},
    )

    assert bal_resp.status_code == 200
    bal_data = bal_resp.json()
    assert bal_data["account"]["balance"] == "$5,150.00"
    assert bal_data["account"]["available_balance"] == "$5,150.00"

    assert len(bal_data["recent_transactions"]) >= 1
    withdrawal_found = any(
        "Withdrawal" in txn["description"] for txn in bal_data["recent_transactions"]
    )
    assert withdrawal_found
