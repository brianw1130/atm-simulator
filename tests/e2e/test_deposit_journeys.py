"""E2E tests for deposit journeys.

E2E-DEP-01 through E2E-DEP-05 as specified in CLAUDE.md.
Each test is independent with fresh database state.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.atm.models.account import Account
from src.atm.models.transaction import Transaction, TransactionType
from tests.e2e.conftest import seed_e2e_data
from tests.factories import create_test_card


async def _login(client: AsyncClient, card_number: str, pin: str) -> str:
    """Helper: login and return the session ID."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"card_number": card_number, "pin": pin},
    )
    assert resp.status_code == 200
    return resp.json()["session_id"]


@pytest.mark.asyncio
async def test_e2e_dep_01_cash_deposit_standard(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """E2E-DEP-01: Cash Deposit $500 (hold applied)."""
    data = await seed_e2e_data(db_session)
    session_id = await _login(client, data["bob_card_number"], "5678")

    resp = await client.post(
        "/api/v1/transactions/deposit",
        json={"amount_cents": 50_000, "deposit_type": "cash"},
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 201
    resp_data = resp.json()
    assert resp_data["transaction_type"] == "DEPOSIT_CASH"
    assert resp_data["amount"] == "$500.00"
    assert resp_data["available_immediately"] == "$200.00"
    assert resp_data["held_amount"] == "$300.00"
    assert resp_data["hold_until"] is not None
    assert "reference_number" in resp_data

    acct_stmt = select(Account).where(Account.id == data["bob_checking"].id)
    acct_result = await db_session.execute(acct_stmt)
    account = acct_result.scalars().first()
    assert account is not None
    assert account.balance_cents == 85_075 + 50_000
    assert account.available_balance_cents == 85_075 + 20_000


@pytest.mark.asyncio
async def test_e2e_dep_02_cash_deposit_small_amount(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """E2E-DEP-02: Cash Deposit $150 (full immediate availability)."""
    data = await seed_e2e_data(db_session)
    session_id = await _login(client, data["bob_card_number"], "5678")

    resp = await client.post(
        "/api/v1/transactions/deposit",
        json={"amount_cents": 15_000, "deposit_type": "cash"},
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 201
    resp_data = resp.json()
    assert resp_data["available_immediately"] == "$150.00"
    assert resp_data["held_amount"] == "$0.00"
    assert resp_data["hold_until"] is None

    acct_stmt = select(Account).where(Account.id == data["bob_checking"].id)
    acct_result = await db_session.execute(acct_stmt)
    account = acct_result.scalars().first()
    assert account is not None
    assert account.balance_cents == 85_075 + 15_000
    assert account.available_balance_cents == 85_075 + 15_000


@pytest.mark.asyncio
async def test_e2e_dep_03_check_deposit(client: AsyncClient, db_session: AsyncSession) -> None:
    """E2E-DEP-03: Check Deposit $1,000 with check #4521."""
    data = await seed_e2e_data(db_session)
    session_id = await _login(client, data["bob_card_number"], "5678")

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
    resp_data = resp.json()
    assert resp_data["transaction_type"] == "DEPOSIT_CHECK"
    assert resp_data["amount"] == "$1,000.00"
    assert resp_data["available_immediately"] == "$0.00"
    assert resp_data["held_amount"] == "$1,000.00"
    assert resp_data["hold_until"] is not None
    assert "reference_number" in resp_data

    acct_stmt = select(Account).where(Account.id == data["bob_checking"].id)
    acct_result = await db_session.execute(acct_stmt)
    account = acct_result.scalars().first()
    assert account is not None
    assert account.balance_cents == 85_075 + 100_000
    assert account.available_balance_cents == 85_075

    txn_stmt = (
        select(Transaction)
        .where(Transaction.account_id == data["bob_checking"].id)
        .where(Transaction.transaction_type == TransactionType.DEPOSIT_CHECK)
    )
    txn_result = await db_session.execute(txn_stmt)
    txn = txn_result.scalars().first()
    assert txn is not None
    assert txn.check_number == "4521"
    assert txn.hold_until is not None


@pytest.mark.asyncio
async def test_e2e_dep_04_deposit_to_savings(client: AsyncClient, db_session: AsyncSession) -> None:
    """E2E-DEP-04: Deposit $300 cash to Alice's savings."""
    data = await seed_e2e_data(db_session)

    import uuid

    savings_card_number = f"4001-0001-{uuid.uuid4().hex[:4]}"
    await create_test_card(
        db_session,
        account_id=data["alice_savings"].id,
        card_number=savings_card_number,
        pin="7856",
    )
    await db_session.commit()

    session_id = await _login(client, savings_card_number, "7856")

    resp = await client.post(
        "/api/v1/transactions/deposit",
        json={"amount_cents": 30_000, "deposit_type": "cash"},
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 201
    resp_data = resp.json()
    assert resp_data["amount"] == "$300.00"
    assert resp_data["available_immediately"] == "$200.00"
    assert resp_data["held_amount"] == "$100.00"

    acct_stmt = select(Account).where(Account.id == data["alice_savings"].id)
    acct_result = await db_session.execute(acct_stmt)
    account = acct_result.scalars().first()
    assert account is not None
    assert account.balance_cents == 1_250_000 + 30_000


@pytest.mark.asyncio
async def test_e2e_dep_05_multiple_deposits_single_session(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """E2E-DEP-05: Multiple Deposits ($200 cash + $500 check)."""
    data = await seed_e2e_data(db_session)
    session_id = await _login(client, data["bob_card_number"], "5678")
    initial_balance = 85_075

    # Cash deposit $200 (at threshold, full immediate)
    resp1 = await client.post(
        "/api/v1/transactions/deposit",
        json={"amount_cents": 20_000, "deposit_type": "cash"},
        headers={"X-Session-ID": session_id},
    )
    assert resp1.status_code == 201
    assert resp1.json()["available_immediately"] == "$200.00"
    assert resp1.json()["held_amount"] == "$0.00"

    # Check deposit $500 (all held)
    resp2 = await client.post(
        "/api/v1/transactions/deposit",
        json={
            "amount_cents": 50_000,
            "deposit_type": "check",
            "check_number": "9876",
        },
        headers={"X-Session-ID": session_id},
    )
    assert resp2.status_code == 201
    assert resp2.json()["available_immediately"] == "$0.00"
    assert resp2.json()["held_amount"] == "$500.00"

    # Verify both transactions recorded
    txn_stmt = (
        select(Transaction)
        .where(Transaction.account_id == data["bob_checking"].id)
        .order_by(Transaction.created_at.asc())
    )
    txn_result = await db_session.execute(txn_stmt)
    txns = list(txn_result.scalars().all())
    assert len(txns) == 2
    assert txns[0].transaction_type == TransactionType.DEPOSIT_CASH
    assert txns[1].transaction_type == TransactionType.DEPOSIT_CHECK

    acct_stmt = select(Account).where(Account.id == data["bob_checking"].id)
    acct_result = await db_session.execute(acct_stmt)
    account = acct_result.scalars().first()
    assert account is not None
    assert account.balance_cents == initial_balance + 20_000 + 50_000
    assert account.available_balance_cents == initial_balance + 20_000
