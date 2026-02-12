"""Unit tests for CashCassette model.

Coverage requirement: 100%

Tests: model creation with all fields, default values.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.atm.models.cassette import CashCassette

pytestmark = pytest.mark.asyncio


class TestCashCassetteModel:
    async def test_create_with_all_fields(self, db_session: AsyncSession) -> None:
        """CashCassette can be created with explicit values for all fields."""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        cassette = CashCassette(
            denomination_cents=2000,
            bill_count=500,
            max_capacity=2000,
            last_refilled_at=now,
        )
        db_session.add(cassette)
        await db_session.flush()

        assert cassette.id is not None
        assert cassette.denomination_cents == 2000
        assert cassette.bill_count == 500
        assert cassette.max_capacity == 2000
        assert cassette.last_refilled_at == now
        assert cassette.created_at is not None

    async def test_default_bill_count_is_zero(self, db_session: AsyncSession) -> None:
        """bill_count defaults to 0 when not specified."""
        cassette = CashCassette(denomination_cents=2000)
        db_session.add(cassette)
        await db_session.flush()

        assert cassette.bill_count == 0

    async def test_default_max_capacity_is_2000(
        self, db_session: AsyncSession
    ) -> None:
        """max_capacity defaults to 2000 when not specified."""
        cassette = CashCassette(denomination_cents=2000)
        db_session.add(cassette)
        await db_session.flush()

        assert cassette.max_capacity == 2000

    async def test_last_refilled_at_nullable(self, db_session: AsyncSession) -> None:
        """last_refilled_at can be None."""
        cassette = CashCassette(denomination_cents=2000, bill_count=10)
        db_session.add(cassette)
        await db_session.flush()

        assert cassette.last_refilled_at is None

    async def test_tablename(self) -> None:
        """The table name is 'cash_cassettes'."""
        assert CashCassette.__tablename__ == "cash_cassettes"
