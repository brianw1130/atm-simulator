"""Integration tests for deposit API endpoints.

Tests cover: cash deposit <= $200 (full availability), cash deposit > $200 (hold),
check deposit with hold, missing check_number for check deposit.
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


async def _setup_bob(db_session: AsyncSession) -> None:
    """Seed Bob with checking account ($850.75) and card."""
    customer = await create_test_customer(db_session, first_name="Bob", last_name="Williams")
    await create_test_account(
        db_session,
        customer_id=customer.id,
        account_number="1000-0002-0001",
        balance_cents=85_075,
    )
    await create_test_card(
        db_session,
        account_id=1,
        card_number="4000-0002-0001",
        pin="5678",
    )
    await db_session.commit()


@pytest.mark.asyncio
async def test_cash_deposit_small_amount(client: AsyncClient, db_session: AsyncSession) -> None:
    """Cash deposit <= $200 makes full amount available immediately."""
    await _setup_bob(db_session)
    session_id = await _login(client, "4000-0002-0001", "5678")

    resp = await client.post(
        "/api/v1/transactions/deposit",
        json={"amount_cents": 15_000, "deposit_type": "cash"},
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["transaction_type"] == "DEPOSIT_CASH"
    assert data["amount"] == "$150.00"
    assert data["available_immediately"] == "$150.00"
    assert data["held_amount"] == "$0.00"
    assert data["hold_until"] is None
    assert "reference_number" in data


@pytest.mark.asyncio
async def test_cash_deposit_large_amount_with_hold(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Cash deposit > $200: first $200 immediate, remainder held."""
    await _setup_bob(db_session)
    session_id = await _login(client, "4000-0002-0001", "5678")

    resp = await client.post(
        "/api/v1/transactions/deposit",
        json={"amount_cents": 50_000, "deposit_type": "cash"},
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["transaction_type"] == "DEPOSIT_CASH"
    assert data["amount"] == "$500.00"
    assert data["available_immediately"] == "$200.00"
    assert data["held_amount"] == "$300.00"
    assert data["hold_until"] is not None


@pytest.mark.asyncio
async def test_check_deposit_with_hold(client: AsyncClient, db_session: AsyncSession) -> None:
    """Check deposit applies hold policy and includes check_number."""
    await _setup_bob(db_session)
    session_id = await _login(client, "4000-0002-0001", "5678")

    resp = await client.post(
        "/api/v1/transactions/deposit",
        json={
            "amount_cents": 100_000,
            "deposit_type": "check",
            "check_number": "4521",
        },
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["transaction_type"] == "DEPOSIT_CHECK"
    assert data["amount"] == "$1,000.00"
    assert data["available_immediately"] == "$0.00"
    assert data["held_amount"] == "$1,000.00"
    assert data["hold_until"] is not None
    assert "reference_number" in data


@pytest.mark.asyncio
async def test_check_deposit_missing_check_number(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Check deposit without check_number returns 400 (service validation)."""
    await _setup_bob(db_session)
    session_id = await _login(client, "4000-0002-0001", "5678")

    resp = await client.post(
        "/api/v1/transactions/deposit",
        json={"amount_cents": 50_000, "deposit_type": "check"},
        headers={"X-Session-ID": session_id},
    )

    # check_number defaults to None; service catches this and returns 400
    assert resp.status_code == 400
    assert "check number" in resp.json()["detail"].lower()
