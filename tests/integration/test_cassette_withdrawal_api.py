"""Integration tests for cash cassette integration with withdrawal API.

Tests cover:
    - Withdrawal succeeds when cassette has enough bills, bill_count decremented
    - Withdrawal fails when cassette is empty ("Insufficient bills available")
    - Withdrawal works normally when no cassettes configured (backward compat)
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.atm.models.cassette import CashCassette
from tests.factories import create_test_account, create_test_card, create_test_customer

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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


async def _add_cassette(
    db_session: AsyncSession,
    bill_count: int = 100,
) -> None:
    """Add a $20 cassette with the given bill_count."""
    cassette = CashCassette(
        denomination_cents=2000,
        bill_count=bill_count,
        max_capacity=2000,
    )
    db_session.add(cassette)
    await db_session.flush()
    await db_session.commit()


# ===========================================================================
# Tests
# ===========================================================================


class TestCassetteWithdrawalIntegration:
    async def test_withdrawal_succeeds_with_enough_bills(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Withdrawal succeeds and decrements cassette bill_count."""
        await _setup_alice(db_session)
        await _add_cassette(db_session, bill_count=100)
        session_id = await _login(client, "4000-0001-0001", "7856")

        resp = await client.post(
            "/api/v1/transactions/withdraw",
            json={"amount_cents": 10_000},  # $100 = 5 x $20 bills
            headers={"X-Session-ID": session_id},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["denominations"]["twenties"] == 5

        # Verify bill_count was decremented
        stmt = select(CashCassette).where(CashCassette.denomination_cents == 2000)
        result = await db_session.execute(stmt)
        cassette = result.scalars().first()
        assert cassette is not None
        assert cassette.bill_count == 95  # 100 - 5

    async def test_withdrawal_fails_when_cassette_empty(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Withdrawal fails with 'Insufficient bills' when cassette has too few bills."""
        await _setup_alice(db_session)
        await _add_cassette(db_session, bill_count=2)  # Only 2 bills = $40
        session_id = await _login(client, "4000-0001-0001", "7856")

        resp = await client.post(
            "/api/v1/transactions/withdraw",
            json={"amount_cents": 10_000},  # $100 = 5 bills needed
            headers={"X-Session-ID": session_id},
        )
        assert resp.status_code == 400
        assert "Insufficient bills" in resp.json()["detail"]

    async def test_withdrawal_works_without_cassettes_backward_compat(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Withdrawal works normally when no cassettes are configured."""
        await _setup_alice(db_session)
        # No cassette added — backward compatibility mode
        session_id = await _login(client, "4000-0001-0001", "7856")

        resp = await client.post(
            "/api/v1/transactions/withdraw",
            json={"amount_cents": 10_000},
            headers={"X-Session-ID": session_id},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["denominations"]["twenties"] == 5
        assert data["balance_after"] == "$5,150.00"
