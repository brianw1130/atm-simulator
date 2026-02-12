"""Integration tests for transfer API endpoints.

Tests cover: own-account transfer, external transfer, insufficient funds,
daily limit exceeded, transfer to nonexistent account, transfer to self.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.atm.models.account import AccountType
from tests.factories import create_test_account, create_test_card, create_test_customer


async def _login(client: AsyncClient, card_number: str, pin: str) -> str:
    """Helper: login and return the session ID."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"card_number": card_number, "pin": pin},
    )
    assert resp.status_code == 200
    return resp.json()["session_id"]


async def _setup_alice_with_both_accounts(db_session: AsyncSession) -> dict:
    """Seed Alice with checking ($5,250) and savings ($12,500) accounts."""
    customer = await create_test_customer(
        db_session, first_name="Alice", last_name="Johnson"
    )
    checking = await create_test_account(
        db_session,
        customer_id=customer.id,
        account_number="1000-0001-0001",
        account_type=AccountType.CHECKING,
        balance_cents=525_000,
    )
    savings = await create_test_account(
        db_session,
        customer_id=customer.id,
        account_number="1000-0001-0002",
        account_type=AccountType.SAVINGS,
        balance_cents=1_250_000,
    )
    card = await create_test_card(
        db_session,
        account_id=checking.id,
        card_number="4000-0001-0001",
        pin="7856",
    )
    await db_session.commit()
    return {
        "customer": customer,
        "checking": checking,
        "savings": savings,
        "card": card,
    }


@pytest.mark.asyncio
async def test_transfer_own_accounts(client: AsyncClient, db_session: AsyncSession) -> None:
    """Transfer $1,000 from checking to savings returns 201."""
    await _setup_alice_with_both_accounts(db_session)
    session_id = await _login(client, "4000-0001-0001", "7856")

    resp = await client.post(
        "/api/v1/transactions/transfer",
        json={
            "destination_account_number": "1000-0001-0002",
            "amount_cents": 100_000,
        },
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["transaction_type"] == "TRANSFER_OUT"
    assert data["amount"] == "$1,000.00"
    assert data["balance_after"] == "$4,250.00"
    assert "reference_number" in data
    assert "source_account" in data
    assert "destination_account" in data


@pytest.mark.asyncio
async def test_transfer_external_account(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Transfer to another customer's account returns 201."""
    alice_data = await _setup_alice_with_both_accounts(db_session)

    # Create Bob's account
    bob = await create_test_customer(
        db_session, first_name="Bob", last_name="Williams"
    )
    await create_test_account(
        db_session,
        customer_id=bob.id,
        account_number="1000-0002-0001",
        balance_cents=85_075,
    )
    await db_session.commit()

    session_id = await _login(client, "4000-0001-0001", "7856")

    resp = await client.post(
        "/api/v1/transactions/transfer",
        json={
            "destination_account_number": "1000-0002-0001",
            "amount_cents": 20_000,
        },
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["amount"] == "$200.00"


@pytest.mark.asyncio
async def test_transfer_insufficient_funds(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Transfer more than available balance returns 400."""
    customer = await create_test_customer(
        db_session, first_name="Charlie", last_name="Davis"
    )
    checking = await create_test_account(
        db_session,
        customer_id=customer.id,
        account_number="1000-0003-0001",
        balance_cents=0,
    )
    savings = await create_test_account(
        db_session,
        customer_id=customer.id,
        account_number="1000-0003-0002",
        account_type=AccountType.SAVINGS,
        balance_cents=10_000,
    )
    await create_test_card(
        db_session,
        account_id=checking.id,
        card_number="4000-0003-0001",
        pin="9012",
    )
    await db_session.commit()

    session_id = await _login(client, "4000-0003-0001", "9012")

    resp = await client.post(
        "/api/v1/transactions/transfer",
        json={
            "destination_account_number": "1000-0003-0002",
            "amount_cents": 5_000,
        },
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 400
    assert "insufficient" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_transfer_daily_limit_exceeded(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Second transfer exceeding $2,500 daily limit returns 400."""
    await _setup_alice_with_both_accounts(db_session)
    session_id = await _login(client, "4000-0001-0001", "7856")

    # First transfer of $2,000
    resp1 = await client.post(
        "/api/v1/transactions/transfer",
        json={
            "destination_account_number": "1000-0001-0002",
            "amount_cents": 200_000,
        },
        headers={"X-Session-ID": session_id},
    )
    assert resp1.status_code == 201

    # Second transfer of $1,000 exceeds $2,500 limit
    resp2 = await client.post(
        "/api/v1/transactions/transfer",
        json={
            "destination_account_number": "1000-0001-0002",
            "amount_cents": 100_000,
        },
        headers={"X-Session-ID": session_id},
    )
    assert resp2.status_code == 400
    assert "daily" in resp2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_transfer_to_nonexistent_account(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Transfer to a nonexistent account returns 400."""
    await _setup_alice_with_both_accounts(db_session)
    session_id = await _login(client, "4000-0001-0001", "7856")

    resp = await client.post(
        "/api/v1/transactions/transfer",
        json={
            "destination_account_number": "9999-9999-9999",
            "amount_cents": 10_000,
        },
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 400
    assert "not found" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_transfer_to_same_account(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Transfer to the same account (self-transfer) returns 400."""
    await _setup_alice_with_both_accounts(db_session)
    session_id = await _login(client, "4000-0001-0001", "7856")

    resp = await client.post(
        "/api/v1/transactions/transfer",
        json={
            "destination_account_number": "1000-0001-0001",
            "amount_cents": 10_000,
        },
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 400
    assert "same account" in resp.json()["detail"].lower()
