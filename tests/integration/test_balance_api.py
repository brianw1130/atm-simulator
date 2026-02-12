"""Integration tests for balance inquiry API endpoints.

Tests cover: get balance, balance after withdrawal, nonexistent account.
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


@pytest.mark.asyncio
async def test_get_balance(client: AsyncClient, db_session: AsyncSession) -> None:
    """Get balance returns 200 with account summary and recent transactions."""
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

    session_id = await _login(client, "4000-0001-0001", "7856")

    resp = await client.get(
        f"/api/v1/accounts/{account.id}/balance",
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert "account" in data
    assert data["account"]["balance"] == "$5,250.00"
    assert data["account"]["available_balance"] == "$5,250.00"
    assert "recent_transactions" in data
    assert isinstance(data["recent_transactions"], list)


@pytest.mark.asyncio
async def test_get_balance_after_withdrawal(client: AsyncClient, db_session: AsyncSession) -> None:
    """Balance reflects the withdrawal performed in the same session."""
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

    session_id = await _login(client, "4000-0001-0001", "7856")

    # Withdraw $100
    await client.post(
        "/api/v1/transactions/withdraw",
        json={"amount_cents": 10_000},
        headers={"X-Session-ID": session_id},
    )

    # Check balance
    resp = await client.get(
        f"/api/v1/accounts/{account.id}/balance",
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["account"]["balance"] == "$5,150.00"
    # Withdrawal should appear in recent transactions
    assert len(data["recent_transactions"]) >= 1


@pytest.mark.asyncio
async def test_get_balance_nonexistent_account(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Balance inquiry for an account not owned by the user returns 403."""
    customer = await create_test_customer(db_session)
    account = await create_test_account(
        db_session,
        customer_id=customer.id,
        account_number="1000-0099-0001",
    )
    await create_test_card(
        db_session,
        account_id=account.id,
        card_number="4000-0099-0001",
        pin="7856",
    )
    await db_session.commit()

    session_id = await _login(client, "4000-0099-0001", "7856")

    resp = await client.get(
        "/api/v1/accounts/99999/balance",
        headers={"X-Session-ID": session_id},
    )

    # The IDOR protection returns 403 for accounts not owned by the customer
    assert resp.status_code == 403
