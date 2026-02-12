"""E2E tests for error handling and edge case journeys.

E2E-ERR-01, E2E-ERR-03, E2E-ERR-04 as specified in CLAUDE.md.
Each test is independent with fresh database state.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.atm.models.account import Account, AccountStatus
from src.atm.models.transaction import Transaction
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
async def test_e2e_err_01_frozen_account_operations(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """E2E-ERR-01: Frozen Account Operations."""
    data = await seed_e2e_data(db_session)

    # Freeze Bob's account
    bob_account = data["bob_checking"]
    bob_account.status = AccountStatus.FROZEN
    await db_session.flush()
    await db_session.commit()

    # Bob can still authenticate (card-level)
    session_id = await _login(client, data["bob_card_number"], "5678")

    # Withdrawal rejected
    w_resp = await client.post(
        "/api/v1/transactions/withdraw",
        json={"amount_cents": 2_000},
        headers={"X-Session-ID": session_id},
    )
    assert w_resp.status_code == 403
    assert "frozen" in w_resp.json()["detail"].lower()

    # Deposit rejected
    d_resp = await client.post(
        "/api/v1/transactions/deposit",
        json={"amount_cents": 5_000, "deposit_type": "cash"},
        headers={"X-Session-ID": session_id},
    )
    assert d_resp.status_code == 403
    assert "frozen" in d_resp.json()["detail"].lower()

    # Transfer rejected
    t_resp = await client.post(
        "/api/v1/transactions/transfer",
        json={
            "destination_account_number": data["alice_checking_number"],
            "amount_cents": 5_000,
        },
        headers={"X-Session-ID": session_id},
    )
    assert t_resp.status_code == 403
    assert "frozen" in t_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_e2e_err_03_negative_amount_injection(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """E2E-ERR-03: Negative Amount Injection."""
    data = await seed_e2e_data(db_session)
    session_id = await _login(client, data["alice_card_number"], "7856")

    # Negative withdrawal
    w_resp = await client.post(
        "/api/v1/transactions/withdraw",
        json={"amount_cents": -10_000},
        headers={"X-Session-ID": session_id},
    )
    assert w_resp.status_code == 422

    # Negative transfer
    t_resp = await client.post(
        "/api/v1/transactions/transfer",
        json={
            "destination_account_number": data["alice_savings_number"],
            "amount_cents": -5_000,
        },
        headers={"X-Session-ID": session_id},
    )
    assert t_resp.status_code == 422

    # Negative deposit
    d_resp = await client.post(
        "/api/v1/transactions/deposit",
        json={"amount_cents": -20_000, "deposit_type": "cash"},
        headers={"X-Session-ID": session_id},
    )
    assert d_resp.status_code == 422

    # Verify no transactions created
    txn_stmt = select(Transaction).where(Transaction.account_id == data["alice_checking"].id)
    txns = list((await db_session.execute(txn_stmt)).scalars().all())
    assert len(txns) == 0

    # Verify no balance changes
    acct_stmt = select(Account).where(Account.id == data["alice_checking"].id)
    account = (await db_session.execute(acct_stmt)).scalars().first()
    assert account is not None
    assert account.balance_cents == 525_000


@pytest.mark.asyncio
async def test_e2e_err_04_maximum_value_boundaries(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """E2E-ERR-04: Maximum Value Boundaries."""
    data = await seed_e2e_data(db_session)
    session_id = await _login(client, data["alice_card_number"], "7856")

    # Large deposit: $999,999.99
    d_resp = await client.post(
        "/api/v1/transactions/deposit",
        json={"amount_cents": 99_999_999, "deposit_type": "cash"},
        headers={"X-Session-ID": session_id},
    )

    assert d_resp.status_code == 201
    assert d_resp.json()["amount"] == "$999,999.99"

    # Verify balance updated correctly (no overflow)
    acct_stmt = select(Account).where(Account.id == data["alice_checking"].id)
    account = (await db_session.execute(acct_stmt)).scalars().first()
    assert account is not None
    expected_balance = 525_000 + 99_999_999
    assert account.balance_cents == expected_balance

    # Large transfer: should be rejected by daily transfer limit ($2,500).
    # After the deposit, available_balance is $5,250 + $200 (hold policy) = $5,450,
    # so we use $3,000 which is within available balance but above $2,500 daily limit.
    t_resp = await client.post(
        "/api/v1/transactions/transfer",
        json={
            "destination_account_number": data["alice_savings_number"],
            "amount_cents": 300_000,  # $3,000 > $2,500 daily transfer limit
        },
        headers={"X-Session-ID": session_id},
    )
    assert t_resp.status_code == 400
    assert "daily" in t_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_e2e_err_zero_amounts(client: AsyncClient, db_session: AsyncSession) -> None:
    """Zero amounts are rejected by Pydantic (gt=0)."""
    data = await seed_e2e_data(db_session)
    session_id = await _login(client, data["alice_card_number"], "7856")

    w_resp = await client.post(
        "/api/v1/transactions/withdraw",
        json={"amount_cents": 0},
        headers={"X-Session-ID": session_id},
    )
    assert w_resp.status_code == 422

    d_resp = await client.post(
        "/api/v1/transactions/deposit",
        json={"amount_cents": 0, "deposit_type": "cash"},
        headers={"X-Session-ID": session_id},
    )
    assert d_resp.status_code == 422

    t_resp = await client.post(
        "/api/v1/transactions/transfer",
        json={
            "destination_account_number": data["alice_savings_number"],
            "amount_cents": 0,
        },
        headers={"X-Session-ID": session_id},
    )
    assert t_resp.status_code == 422
