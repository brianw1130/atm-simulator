"""E2E tests for transfer journeys.

E2E-TRF-01 through E2E-TRF-07 as specified in CLAUDE.md.
Each test is independent with fresh database state.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.atm.models.account import Account
from src.atm.models.audit import AuditEventType, AuditLog
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
async def test_e2e_trf_01_own_account_checking_to_savings(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """E2E-TRF-01: Transfer $1,000 checking -> savings."""
    data = await seed_e2e_data(db_session)
    session_id = await _login(client, data["alice_card_number"], "7856")

    resp = await client.post(
        "/api/v1/transactions/transfer",
        json={
            "destination_account_number": data["alice_savings_number"],
            "amount_cents": 100_000,
        },
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 201
    resp_data = resp.json()
    assert resp_data["transaction_type"] == "TRANSFER_OUT"
    assert resp_data["amount"] == "$1,000.00"
    assert resp_data["balance_after"] == "$4,250.00"
    assert "reference_number" in resp_data
    assert "source_account" in resp_data
    assert "destination_account" in resp_data

    # Verify checking balance reduced
    checking_stmt = select(Account).where(Account.id == data["alice_checking"].id)
    checking_result = await db_session.execute(checking_stmt)
    checking = checking_result.scalars().first()
    assert checking is not None
    assert checking.balance_cents == 425_000

    # Verify savings balance increased
    savings_stmt = select(Account).where(Account.id == data["alice_savings"].id)
    savings_result = await db_session.execute(savings_stmt)
    savings = savings_result.scalars().first()
    assert savings is not None
    assert savings.balance_cents == 1_350_000

    # Verify TRANSFER_OUT on source
    txn_out_stmt = (
        select(Transaction)
        .where(Transaction.account_id == data["alice_checking"].id)
        .where(Transaction.transaction_type == TransactionType.TRANSFER_OUT)
    )
    txn_out_result = await db_session.execute(txn_out_stmt)
    txn_out = txn_out_result.scalars().first()
    assert txn_out is not None
    assert txn_out.amount_cents == 100_000
    assert txn_out.related_account_id == data["alice_savings"].id

    # Verify TRANSFER_IN on destination
    txn_in_stmt = (
        select(Transaction)
        .where(Transaction.account_id == data["alice_savings"].id)
        .where(Transaction.transaction_type == TransactionType.TRANSFER_IN)
    )
    txn_in_result = await db_session.execute(txn_in_stmt)
    txn_in = txn_in_result.scalars().first()
    assert txn_in is not None
    assert txn_in.amount_cents == 100_000
    assert txn_in.related_account_id == data["alice_checking"].id


@pytest.mark.asyncio
async def test_e2e_trf_02_own_account_savings_to_checking(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """E2E-TRF-02: Transfer $500 savings -> checking."""
    data = await seed_e2e_data(db_session)

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
        "/api/v1/transactions/transfer",
        json={
            "destination_account_number": data["alice_checking_number"],
            "amount_cents": 50_000,
        },
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 201
    assert resp.json()["amount"] == "$500.00"

    savings_stmt = select(Account).where(Account.id == data["alice_savings"].id)
    savings_result = await db_session.execute(savings_stmt)
    savings = savings_result.scalars().first()
    assert savings is not None
    assert savings.balance_cents == 1_200_000

    checking_stmt = select(Account).where(Account.id == data["alice_checking"].id)
    checking_result = await db_session.execute(checking_stmt)
    checking = checking_result.scalars().first()
    assert checking is not None
    assert checking.balance_cents == 575_000


@pytest.mark.asyncio
async def test_e2e_trf_03_external_transfer(client: AsyncClient, db_session: AsyncSession) -> None:
    """E2E-TRF-03: Transfer $200 from Alice to Bob."""
    data = await seed_e2e_data(db_session)
    session_id = await _login(client, data["alice_card_number"], "7856")

    resp = await client.post(
        "/api/v1/transactions/transfer",
        json={
            "destination_account_number": data["bob_checking_number"],
            "amount_cents": 20_000,
        },
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 201
    assert resp.json()["amount"] == "$200.00"

    alice_stmt = select(Account).where(Account.id == data["alice_checking"].id)
    alice_result = await db_session.execute(alice_stmt)
    alice = alice_result.scalars().first()
    assert alice is not None
    assert alice.balance_cents == 505_000

    bob_stmt = select(Account).where(Account.id == data["bob_checking"].id)
    bob_result = await db_session.execute(bob_stmt)
    bob = bob_result.scalars().first()
    assert bob is not None
    assert bob.balance_cents == 105_075

    # Verify related_account_id on both transactions
    txn_out_stmt = (
        select(Transaction)
        .where(Transaction.account_id == data["alice_checking"].id)
        .where(Transaction.transaction_type == TransactionType.TRANSFER_OUT)
    )
    txn_out = (await db_session.execute(txn_out_stmt)).scalars().first()
    assert txn_out is not None
    assert txn_out.related_account_id == data["bob_checking"].id

    txn_in_stmt = (
        select(Transaction)
        .where(Transaction.account_id == data["bob_checking"].id)
        .where(Transaction.transaction_type == TransactionType.TRANSFER_IN)
    )
    txn_in = (await db_session.execute(txn_in_stmt)).scalars().first()
    assert txn_in is not None
    assert txn_in.related_account_id == data["alice_checking"].id


@pytest.mark.asyncio
async def test_e2e_trf_04_transfer_insufficient_funds(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """E2E-TRF-04: Transfer from Charlie ($0) -> rejected."""
    data = await seed_e2e_data(db_session)
    session_id = await _login(client, data["charlie_card_number"], "9012")

    resp = await client.post(
        "/api/v1/transactions/transfer",
        json={
            "destination_account_number": data["alice_checking_number"],
            "amount_cents": 5_000,
        },
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 400
    assert "insufficient" in resp.json()["detail"].lower()

    # Verify no balance changes
    charlie_stmt = select(Account).where(Account.id == data["charlie_checking"].id)
    charlie = (await db_session.execute(charlie_stmt)).scalars().first()
    assert charlie is not None
    assert charlie.balance_cents == 0

    alice_stmt = select(Account).where(Account.id == data["alice_checking"].id)
    alice = (await db_session.execute(alice_stmt)).scalars().first()
    assert alice is not None
    assert alice.balance_cents == 525_000


@pytest.mark.asyncio
async def test_e2e_trf_05_transfer_exceeds_daily_limit(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """E2E-TRF-05: Transfer $2,000 then $1,000 (exceeds $2,500 limit)."""
    data = await seed_e2e_data(db_session)
    session_id = await _login(client, data["alice_card_number"], "7856")

    resp1 = await client.post(
        "/api/v1/transactions/transfer",
        json={
            "destination_account_number": data["alice_savings_number"],
            "amount_cents": 200_000,
        },
        headers={"X-Session-ID": session_id},
    )
    assert resp1.status_code == 201

    resp2 = await client.post(
        "/api/v1/transactions/transfer",
        json={
            "destination_account_number": data["alice_savings_number"],
            "amount_cents": 100_000,
        },
        headers={"X-Session-ID": session_id},
    )
    assert resp2.status_code == 400
    assert "daily" in resp2.json()["detail"].lower()

    checking_stmt = select(Account).where(Account.id == data["alice_checking"].id)
    checking = (await db_session.execute(checking_stmt)).scalars().first()
    assert checking is not None
    assert checking.balance_cents == 325_000


@pytest.mark.asyncio
async def test_e2e_trf_06_transfer_to_nonexistent_account(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """E2E-TRF-06: Transfer to nonexistent account -> rejected."""
    data = await seed_e2e_data(db_session)
    session_id = await _login(client, data["alice_card_number"], "7856")

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

    alice_stmt = select(Account).where(Account.id == data["alice_checking"].id)
    alice = (await db_session.execute(alice_stmt)).scalars().first()
    assert alice is not None
    assert alice.balance_cents == 525_000

    audit_stmt = select(AuditLog).where(AuditLog.event_type == AuditEventType.TRANSFER_DECLINED)
    audit_entries = list((await db_session.execute(audit_stmt)).scalars().all())
    assert len(audit_entries) >= 1


@pytest.mark.asyncio
async def test_e2e_trf_07_transfer_to_same_account(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """E2E-TRF-07: Transfer to same account -> rejected."""
    data = await seed_e2e_data(db_session)
    session_id = await _login(client, data["alice_card_number"], "7856")

    resp = await client.post(
        "/api/v1/transactions/transfer",
        json={
            "destination_account_number": data["alice_checking_number"],
            "amount_cents": 10_000,
        },
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 400
    assert "same account" in resp.json()["detail"].lower()

    txn_stmt = select(Transaction).where(Transaction.account_id == data["alice_checking"].id)
    txns = list((await db_session.execute(txn_stmt)).scalars().all())
    assert len(txns) == 0
