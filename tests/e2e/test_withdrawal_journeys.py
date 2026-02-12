"""E2E tests for withdrawal journeys.

E2E-WDR-01 through E2E-WDR-07 as specified in CLAUDE.md.
Each test is independent with fresh database state.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.atm.models.account import Account
from src.atm.models.audit import AuditEventType, AuditLog
from src.atm.models.transaction import Transaction, TransactionType
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
async def test_e2e_wdr_01_quick_withdraw_100(client: AsyncClient, db_session: AsyncSession) -> None:
    """E2E-WDR-01: Quick Withdraw $100."""
    data = await seed_e2e_data(db_session)
    session_id = await _login(client, data["alice_card_number"], "7856")

    resp = await client.post(
        "/api/v1/transactions/withdraw",
        json={"amount_cents": 10_000},
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 201
    resp_data = resp.json()

    assert resp_data["transaction_type"] == "WITHDRAWAL"
    assert resp_data["amount"] == "$100.00"
    assert resp_data["balance_after"] == "$5,150.00"
    assert "reference_number" in resp_data
    assert resp_data["denominations"]["twenties"] == 5
    assert resp_data["denominations"]["total_bills"] == 5
    assert resp_data["denominations"]["total_amount"] == "$100.00"

    # Verify database state
    acct_stmt = select(Account).where(Account.id == data["alice_checking"].id)
    acct_result = await db_session.execute(acct_stmt)
    account = acct_result.scalars().first()
    assert account is not None
    assert account.balance_cents == 515_000
    assert account.available_balance_cents == 515_000
    assert account.daily_withdrawal_used_cents == 10_000

    # Verify transaction record
    txn_stmt = select(Transaction).where(Transaction.account_id == data["alice_checking"].id)
    txn_result = await db_session.execute(txn_stmt)
    txns = list(txn_result.scalars().all())
    assert len(txns) == 1
    assert txns[0].transaction_type == TransactionType.WITHDRAWAL
    assert txns[0].amount_cents == 10_000


@pytest.mark.asyncio
async def test_e2e_wdr_02_custom_amount_withdraw(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """E2E-WDR-02: Custom Amount Withdraw $260."""
    data = await seed_e2e_data(db_session)
    session_id = await _login(client, data["alice_card_number"], "7856")

    resp = await client.post(
        "/api/v1/transactions/withdraw",
        json={"amount_cents": 26_000},
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 201
    resp_data = resp.json()
    assert resp_data["amount"] == "$260.00"
    assert resp_data["balance_after"] == "$4,990.00"
    assert resp_data["denominations"]["twenties"] == 13


@pytest.mark.asyncio
async def test_e2e_wdr_03_non_standard_amount_rejected(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """E2E-WDR-03: Non-Standard Amount Rejected ($55)."""
    data = await seed_e2e_data(db_session)
    session_id = await _login(client, data["alice_card_number"], "7856")

    resp = await client.post(
        "/api/v1/transactions/withdraw",
        json={"amount_cents": 5_500},
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 422

    # Verify no balance change
    acct_stmt = select(Account).where(Account.id == data["alice_checking"].id)
    acct_result = await db_session.execute(acct_stmt)
    account = acct_result.scalars().first()
    assert account is not None
    assert account.balance_cents == 525_000

    # Verify no transaction created
    txn_stmt = select(Transaction).where(Transaction.account_id == data["alice_checking"].id)
    txn_result = await db_session.execute(txn_stmt)
    txns = list(txn_result.scalars().all())
    assert len(txns) == 0


@pytest.mark.asyncio
async def test_e2e_wdr_04_insufficient_funds(client: AsyncClient, db_session: AsyncSession) -> None:
    """E2E-WDR-04: Insufficient Funds (Bob $850.75, withdraw $900)."""
    data = await seed_e2e_data(db_session)
    session_id = await _login(client, data["bob_card_number"], "5678")

    resp = await client.post(
        "/api/v1/transactions/withdraw",
        json={"amount_cents": 90_000},
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 400
    assert "insufficient" in resp.json()["detail"].lower()

    # Verify balance unchanged
    acct_stmt = select(Account).where(Account.id == data["bob_checking"].id)
    acct_result = await db_session.execute(acct_stmt)
    account = acct_result.scalars().first()
    assert account is not None
    assert account.balance_cents == 85_075

    # Verify no transaction created
    txn_stmt = select(Transaction).where(Transaction.account_id == data["bob_checking"].id)
    txn_result = await db_session.execute(txn_stmt)
    txns = list(txn_result.scalars().all())
    assert len(txns) == 0

    # Verify audit log records declined transaction
    audit_stmt = select(AuditLog).where(AuditLog.event_type == AuditEventType.WITHDRAWAL_DECLINED)
    audit_result = await db_session.execute(audit_stmt)
    audit_entries = list(audit_result.scalars().all())
    assert len(audit_entries) >= 1


@pytest.mark.asyncio
async def test_e2e_wdr_05_daily_limit_enforcement(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """E2E-WDR-05: Daily Limit Enforcement ($200+$200+$200, limit $500)."""
    data = await seed_e2e_data(db_session)
    session_id = await _login(client, data["alice_card_number"], "7856")

    # First $200
    resp1 = await client.post(
        "/api/v1/transactions/withdraw",
        json={"amount_cents": 20_000},
        headers={"X-Session-ID": session_id},
    )
    assert resp1.status_code == 201
    assert resp1.json()["balance_after"] == "$5,050.00"

    # Second $200
    resp2 = await client.post(
        "/api/v1/transactions/withdraw",
        json={"amount_cents": 20_000},
        headers={"X-Session-ID": session_id},
    )
    assert resp2.status_code == 201
    assert resp2.json()["balance_after"] == "$4,850.00"

    # Third $200 exceeds $500 daily limit
    resp3 = await client.post(
        "/api/v1/transactions/withdraw",
        json={"amount_cents": 20_000},
        headers={"X-Session-ID": session_id},
    )
    assert resp3.status_code == 400
    assert "daily" in resp3.json()["detail"].lower()

    # Verify final balance
    acct_stmt = select(Account).where(Account.id == data["alice_checking"].id)
    acct_result = await db_session.execute(acct_stmt)
    account = acct_result.scalars().first()
    assert account is not None
    assert account.balance_cents == 485_000


@pytest.mark.asyncio
async def test_e2e_wdr_06_withdraw_near_exact_balance(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """E2E-WDR-06: Withdraw $500 from Bob's $850.75 (max daily limit, largest feasible)."""
    data = await seed_e2e_data(db_session)
    session_id = await _login(client, data["bob_card_number"], "5678")

    # $500 is the daily withdrawal limit and the largest multiple-of-$20 within that limit
    resp = await client.post(
        "/api/v1/transactions/withdraw",
        json={"amount_cents": 50_000},
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 201
    resp_data = resp.json()
    assert resp_data["balance_after"] == "$350.75"
    assert resp_data["denominations"]["twenties"] == 25

    acct_stmt = select(Account).where(Account.id == data["bob_checking"].id)
    acct_result = await db_session.execute(acct_stmt)
    account = acct_result.scalars().first()
    assert account is not None
    assert account.balance_cents == 35_075


@pytest.mark.asyncio
async def test_e2e_wdr_07_zero_balance_account(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """E2E-WDR-07: Zero Balance Account (Charlie $0)."""
    data = await seed_e2e_data(db_session)
    session_id = await _login(client, data["charlie_card_number"], "9012")

    resp = await client.post(
        "/api/v1/transactions/withdraw",
        json={"amount_cents": 2_000},
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 400
    assert "insufficient" in resp.json()["detail"].lower()
