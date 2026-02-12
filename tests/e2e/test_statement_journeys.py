"""E2E tests for statement generation journeys.

E2E-STM-01 through E2E-STM-05 as specified in CLAUDE.md.
Each test is independent with fresh database state.
"""

import os
from datetime import date, timedelta

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
async def test_e2e_stm_01_7_day_statement_generation(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """E2E-STM-01: 7-Day Statement after transactions."""
    data = await seed_e2e_data(db_session)
    session_id = await _login(client, data["alice_card_number"], "7856")

    # Perform transactions
    await client.post(
        "/api/v1/transactions/withdraw",
        json={"amount_cents": 10_000},
        headers={"X-Session-ID": session_id},
    )
    await client.post(
        "/api/v1/transactions/deposit",
        json={"amount_cents": 5_000, "deposit_type": "cash"},
        headers={"X-Session-ID": session_id},
    )

    resp = await client.post(
        "/api/v1/statements/generate",
        json={"days": 7},
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 200
    resp_data = resp.json()
    assert "file_path" in resp_data
    assert "period" in resp_data
    assert resp_data["transaction_count"] >= 2
    assert "opening_balance" in resp_data
    assert "closing_balance" in resp_data
    assert os.path.exists(resp_data["file_path"])


@pytest.mark.asyncio
async def test_e2e_stm_02_30_day_statement(client: AsyncClient, db_session: AsyncSession) -> None:
    """E2E-STM-02: 30-Day Statement."""
    data = await seed_e2e_data(db_session)
    session_id = await _login(client, data["alice_card_number"], "7856")

    resp = await client.post(
        "/api/v1/statements/generate",
        json={"days": 30},
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 200
    resp_data = resp.json()
    assert "file_path" in resp_data
    assert resp_data["closing_balance"] == "$5,250.00"
    assert os.path.exists(resp_data["file_path"])


@pytest.mark.asyncio
async def test_e2e_stm_03_custom_date_range(client: AsyncClient, db_session: AsyncSession) -> None:
    """E2E-STM-03: Custom Date Range."""
    data = await seed_e2e_data(db_session)
    session_id = await _login(client, data["alice_card_number"], "7856")

    today = date.today()
    start = (today - timedelta(days=14)).isoformat()
    end = today.isoformat()

    resp = await client.post(
        "/api/v1/statements/generate",
        json={"start_date": start, "end_date": end},
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 200
    resp_data = resp.json()
    assert "file_path" in resp_data
    assert "period" in resp_data
    assert os.path.exists(resp_data["file_path"])


@pytest.mark.asyncio
async def test_e2e_stm_04_empty_statement(client: AsyncClient, db_session: AsyncSession) -> None:
    """E2E-STM-04: Empty Statement (Charlie, $0, no transactions)."""
    data = await seed_e2e_data(db_session)
    session_id = await _login(client, data["charlie_card_number"], "9012")

    resp = await client.post(
        "/api/v1/statements/generate",
        json={"days": 7},
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 200
    resp_data = resp.json()
    assert resp_data["transaction_count"] == 0
    assert resp_data["opening_balance"] == "$0.00"
    assert resp_data["closing_balance"] == "$0.00"
    assert os.path.exists(resp_data["file_path"])


@pytest.mark.asyncio
async def test_e2e_stm_05_statement_after_mixed_operations(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """E2E-STM-05: Statement after withdraw + deposit + transfer."""
    data = await seed_e2e_data(db_session)
    session_id = await _login(client, data["alice_card_number"], "7856")

    # Withdraw $100
    w_resp = await client.post(
        "/api/v1/transactions/withdraw",
        json={"amount_cents": 10_000},
        headers={"X-Session-ID": session_id},
    )
    assert w_resp.status_code == 201

    # Deposit $500 cash
    d_resp = await client.post(
        "/api/v1/transactions/deposit",
        json={"amount_cents": 50_000, "deposit_type": "cash"},
        headers={"X-Session-ID": session_id},
    )
    assert d_resp.status_code == 201

    # Transfer $200 to savings
    t_resp = await client.post(
        "/api/v1/transactions/transfer",
        json={
            "destination_account_number": data["alice_savings_number"],
            "amount_cents": 20_000,
        },
        headers={"X-Session-ID": session_id},
    )
    assert t_resp.status_code == 201

    # Generate statement
    stmt_resp = await client.post(
        "/api/v1/statements/generate",
        json={"days": 7},
        headers={"X-Session-ID": session_id},
    )

    assert stmt_resp.status_code == 200
    stmt_data = stmt_resp.json()
    assert stmt_data["transaction_count"] == 3
    # $5,250 - $100 + $500 - $200 = $5,450
    assert stmt_data["closing_balance"] == "$5,450.00"
    assert stmt_data["opening_balance"] == "$5,250.00"
    assert os.path.exists(stmt_data["file_path"])
