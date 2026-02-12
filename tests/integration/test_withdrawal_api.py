"""Integration tests for withdrawal API endpoints.

Tests cover: successful withdrawal, non-$20 multiple, insufficient funds,
daily limit exceeded, zero/negative amount.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import create_test_account, create_test_card, create_test_customer


async def _login(client: AsyncClient, card_number: str, pin: str) -> str:
    """Helper: login and return the session ID."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"card_number": card_number, "pin": pin},
    )
    assert resp.status_code == 200
    return resp.json()["session_id"]


async def _setup_alice(db_session: AsyncSession) -> None:
    """Seed Alice with checking account ($5,250) and card."""
    customer = await create_test_customer(
        db_session, first_name="Alice", last_name="Johnson"
    )
    await create_test_account(
        db_session,
        customer_id=customer.id,
        account_number="1000-0001-0001",
        balance_cents=525_000,
    )
    await create_test_card(
        db_session,
        account_id=1,
        card_number="4000-0001-0001",
        pin="7856",
    )
    await db_session.commit()


@pytest.mark.asyncio
async def test_successful_withdrawal(client: AsyncClient, db_session: AsyncSession) -> None:
    """Withdraw $100 returns 201 with balance reduced and denomination breakdown."""
    await _setup_alice(db_session)
    session_id = await _login(client, "4000-0001-0001", "7856")

    resp = await client.post(
        "/api/v1/transactions/withdraw",
        json={"amount_cents": 10_000},
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["transaction_type"] == "WITHDRAWAL"
    assert data["amount"] == "$100.00"
    assert data["balance_after"] == "$5,150.00"
    assert "reference_number" in data
    assert data["denominations"]["twenties"] == 5
    assert data["denominations"]["total_bills"] == 5


@pytest.mark.asyncio
async def test_withdrawal_non_twenty_multiple(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Withdraw a non-$20-multiple returns 422 validation error."""
    await _setup_alice(db_session)
    session_id = await _login(client, "4000-0001-0001", "7856")

    resp = await client.post(
        "/api/v1/transactions/withdraw",
        json={"amount_cents": 5_500},  # $55
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_withdrawal_insufficient_funds(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Withdraw more than balance returns 400."""
    customer = await create_test_customer(db_session, first_name="Bob", last_name="Williams")
    account = await create_test_account(
        db_session,
        customer_id=customer.id,
        account_number="1000-0002-0001",
        balance_cents=4_000,  # $40
    )
    await create_test_card(
        db_session,
        account_id=account.id,
        card_number="4000-0002-0001",
        pin="5678",
    )
    await db_session.commit()

    session_id = await _login(client, "4000-0002-0001", "5678")

    resp = await client.post(
        "/api/v1/transactions/withdraw",
        json={"amount_cents": 10_000},  # $100 > $40 balance
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 400
    assert "insufficient" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_withdrawal_daily_limit_exceeded(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Third $200 withdrawal exceeds $500 daily limit and returns 400."""
    await _setup_alice(db_session)
    session_id = await _login(client, "4000-0001-0001", "7856")

    # First $200 withdrawal
    resp1 = await client.post(
        "/api/v1/transactions/withdraw",
        json={"amount_cents": 20_000},
        headers={"X-Session-ID": session_id},
    )
    assert resp1.status_code == 201

    # Second $200 withdrawal
    resp2 = await client.post(
        "/api/v1/transactions/withdraw",
        json={"amount_cents": 20_000},
        headers={"X-Session-ID": session_id},
    )
    assert resp2.status_code == 201

    # Third $200 withdrawal exceeds $500 daily limit
    resp3 = await client.post(
        "/api/v1/transactions/withdraw",
        json={"amount_cents": 20_000},
        headers={"X-Session-ID": session_id},
    )
    assert resp3.status_code == 400
    assert "daily" in resp3.json()["detail"].lower()


@pytest.mark.asyncio
async def test_withdrawal_zero_amount(client: AsyncClient, db_session: AsyncSession) -> None:
    """Withdraw $0 returns 422 (validation: amount must be gt 0)."""
    await _setup_alice(db_session)
    session_id = await _login(client, "4000-0001-0001", "7856")

    resp = await client.post(
        "/api/v1/transactions/withdraw",
        json={"amount_cents": 0},
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_withdrawal_negative_amount(client: AsyncClient, db_session: AsyncSession) -> None:
    """Withdraw a negative amount returns 422."""
    await _setup_alice(db_session)
    session_id = await _login(client, "4000-0001-0001", "7856")

    resp = await client.post(
        "/api/v1/transactions/withdraw",
        json={"amount_cents": -2_000},
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 422
