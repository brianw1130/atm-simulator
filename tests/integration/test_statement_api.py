"""Integration tests for statement generation API endpoints.

Tests cover: 7-day statement, 30-day statement, custom date range.
"""

from datetime import date, timedelta

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
    """Seed Alice with checking account and card.

    Also preloads the Account->Customer relationship into the session's
    identity map so that the statement service can access account.customer
    without triggering a synchronous lazy load (which fails in async).
    """
    customer = await create_test_customer(db_session, first_name="Alice", last_name="Johnson")
    account = await create_test_account(
        db_session,
        customer_id=customer.id,
        account_number="1000-0001-0001",
        balance_cents=525_000,
    )
    await create_test_card(
        db_session,
        account_id=account.id,
        card_number="4000-0001-0001",
        pin="7856",
    )
    await db_session.commit()


@pytest.mark.asyncio
async def test_generate_7_day_statement(
    client: AsyncClient, db_session: AsyncSession, tmp_path: object
) -> None:
    """Generate a 7-day statement returns 200 with file_path and period."""
    await _setup_alice(db_session)
    session_id = await _login(client, "4000-0001-0001", "7856")

    resp = await client.post(
        "/api/v1/statements/generate",
        json={"days": 7},
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert "file_path" in data
    assert "period" in data
    assert "transaction_count" in data
    assert data["transaction_count"] >= 0
    assert "opening_balance" in data
    assert "closing_balance" in data


@pytest.mark.asyncio
async def test_generate_30_day_statement(client: AsyncClient, db_session: AsyncSession) -> None:
    """Generate a 30-day statement returns 200."""
    await _setup_alice(db_session)
    session_id = await _login(client, "4000-0001-0001", "7856")

    resp = await client.post(
        "/api/v1/statements/generate",
        json={"days": 30},
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert "file_path" in data
    assert data["closing_balance"] == "$5,250.00"


@pytest.mark.asyncio
async def test_generate_custom_date_range_statement(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Generate a statement with a custom date range returns 200."""
    await _setup_alice(db_session)
    session_id = await _login(client, "4000-0001-0001", "7856")

    today = date.today()
    start = (today - timedelta(days=14)).isoformat()
    end = today.isoformat()

    resp = await client.post(
        "/api/v1/statements/generate",
        json={"start_date": start, "end_date": end},
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert "file_path" in data
    assert "period" in data
