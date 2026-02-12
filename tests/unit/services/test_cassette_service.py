"""Unit tests for cassette_service.

Coverage requirement: 100%

Tests:
    - get_cassette_status: returns cassette info, empty DB
    - can_dispense: enough bills returns True, not enough returns False,
      no cassettes (backward compat returns True)
    - dispense_bills: deducts bill_count, no cassettes (backward compat)
    - refill_cassette: existing cassette (adds bills, respects max_capacity),
      new cassette (creates)
    - initialize_cassettes: creates default cassettes, already initialized (no-op)
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.atm.models.cassette import CashCassette
from src.atm.services.cassette_service import (
    TWENTY_DOLLAR_CENTS,
    can_dispense,
    dispense_bills,
    get_cassette_status,
    initialize_cassettes,
    refill_cassette,
)

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _add_cassette(
    db_session: AsyncSession,
    *,
    denomination_cents: int = TWENTY_DOLLAR_CENTS,
    bill_count: int = 100,
    max_capacity: int = 2000,
) -> CashCassette:
    """Insert a CashCassette row and return it."""
    cassette = CashCassette(
        denomination_cents=denomination_cents,
        bill_count=bill_count,
        max_capacity=max_capacity,
    )
    db_session.add(cassette)
    await db_session.flush()
    return cassette


# ===========================================================================
# get_cassette_status
# ===========================================================================


class TestGetCassetteStatus:
    async def test_returns_cassette_info(self, db_session: AsyncSession) -> None:
        """Returns list of dicts with denomination, count, capacity, total value."""
        await _add_cassette(db_session, bill_count=50)
        await db_session.commit()

        status = await get_cassette_status(db_session)
        assert len(status) == 1
        entry = status[0]
        assert entry["denomination_cents"] == TWENTY_DOLLAR_CENTS
        assert entry["bill_count"] == 50
        assert entry["max_capacity"] == 2000
        assert entry["total_value_cents"] == TWENTY_DOLLAR_CENTS * 50

    async def test_empty_db_returns_empty_list(self, db_session: AsyncSession) -> None:
        """No cassettes in DB returns an empty list."""
        status = await get_cassette_status(db_session)
        assert status == []

    async def test_multiple_denominations_ordered(
        self, db_session: AsyncSession
    ) -> None:
        """Multiple cassettes are returned ordered by denomination_cents."""
        await _add_cassette(db_session, denomination_cents=5000, bill_count=20)
        await _add_cassette(db_session, denomination_cents=2000, bill_count=100)
        await db_session.commit()

        status = await get_cassette_status(db_session)
        assert len(status) == 2
        assert status[0]["denomination_cents"] == 2000
        assert status[1]["denomination_cents"] == 5000


# ===========================================================================
# can_dispense
# ===========================================================================


class TestCanDispense:
    async def test_enough_bills_returns_true(self, db_session: AsyncSession) -> None:
        """Cassette with enough bills for the requested amount returns True."""
        await _add_cassette(db_session, bill_count=100)  # 100 x $20 = $2,000
        await db_session.commit()

        result = await can_dispense(db_session, 10_000)  # $100 = 5 bills
        assert result is True

    async def test_exact_bills_available_returns_true(
        self, db_session: AsyncSession
    ) -> None:
        """Requesting exactly the number of available bills returns True."""
        await _add_cassette(db_session, bill_count=5)
        await db_session.commit()

        result = await can_dispense(db_session, 10_000)  # 5 bills needed, 5 available
        assert result is True

    async def test_not_enough_bills_returns_false(
        self, db_session: AsyncSession
    ) -> None:
        """Cassette with insufficient bills returns False."""
        await _add_cassette(db_session, bill_count=2)  # 2 x $20 = $40
        await db_session.commit()

        result = await can_dispense(db_session, 10_000)  # $100 = 5 bills needed
        assert result is False

    async def test_no_cassettes_returns_true_backward_compat(
        self, db_session: AsyncSession
    ) -> None:
        """No cassettes configured returns True (backward compatibility)."""
        result = await can_dispense(db_session, 50_000)  # Any amount
        assert result is True

    async def test_zero_amount_returns_true(self, db_session: AsyncSession) -> None:
        """Dispensing $0 is always possible (0 bills needed)."""
        await _add_cassette(db_session, bill_count=0)
        await db_session.commit()

        result = await can_dispense(db_session, 0)
        assert result is True


# ===========================================================================
# dispense_bills
# ===========================================================================


class TestDispenseBills:
    async def test_deducts_bill_count(self, db_session: AsyncSession) -> None:
        """Dispensing bills deducts from the cassette's bill_count."""
        cassette = await _add_cassette(db_session, bill_count=100)
        await db_session.commit()

        result = await dispense_bills(db_session, 10_000)  # $100 = 5 bills
        assert result["twenties"] == 5
        assert result["total_bills"] == 5
        assert result["total_amount"] == "$100.00"

        # Refresh to check the updated bill_count
        await db_session.refresh(cassette)
        assert cassette.bill_count == 95

    async def test_no_cassettes_backward_compat(
        self, db_session: AsyncSession
    ) -> None:
        """With no cassettes, dispense_bills still returns denomination breakdown."""
        result = await dispense_bills(db_session, 6_000)  # $60 = 3 bills
        assert result["twenties"] == 3
        assert result["total_bills"] == 3
        assert result["total_amount"] == "$60.00"

    async def test_dispense_large_amount(self, db_session: AsyncSession) -> None:
        """Dispensing a large amount computes correct bills and deducts."""
        cassette = await _add_cassette(db_session, bill_count=500)
        await db_session.commit()

        result = await dispense_bills(db_session, 50_000)  # $500 = 25 bills
        assert result["twenties"] == 25
        assert result["total_bills"] == 25
        assert result["total_amount"] == "$500.00"

        await db_session.refresh(cassette)
        assert cassette.bill_count == 475


# ===========================================================================
# refill_cassette
# ===========================================================================


class TestRefillCassette:
    async def test_existing_cassette_adds_bills(
        self, db_session: AsyncSession
    ) -> None:
        """Refilling an existing cassette increases the bill_count."""
        cassette = await _add_cassette(db_session, bill_count=50, max_capacity=2000)
        await db_session.commit()

        result = await refill_cassette(db_session, TWENTY_DOLLAR_CENTS, 100)
        assert result["bill_count"] == 150
        assert result["denomination_cents"] == TWENTY_DOLLAR_CENTS

    async def test_existing_cassette_respects_max_capacity(
        self, db_session: AsyncSession
    ) -> None:
        """Refilling beyond max_capacity caps at max_capacity."""
        await _add_cassette(db_session, bill_count=1900, max_capacity=2000)
        await db_session.commit()

        result = await refill_cassette(db_session, TWENTY_DOLLAR_CENTS, 500)
        assert result["bill_count"] == 2000  # capped at max
        assert result["max_capacity"] == 2000

    async def test_new_cassette_created(self, db_session: AsyncSession) -> None:
        """Refilling a denomination that doesn't exist creates a new cassette."""
        result = await refill_cassette(db_session, 5000, 200)  # $50 denomination
        assert result["denomination_cents"] == 5000
        assert result["bill_count"] == 200

    async def test_refill_sets_last_refilled_at(
        self, db_session: AsyncSession
    ) -> None:
        """Refilling updates the last_refilled_at timestamp."""
        cassette = await _add_cassette(db_session, bill_count=10)
        await db_session.commit()

        old_refilled = cassette.last_refilled_at
        await refill_cassette(db_session, TWENTY_DOLLAR_CENTS, 5)

        await db_session.refresh(cassette)
        assert cassette.last_refilled_at is not None


# ===========================================================================
# initialize_cassettes
# ===========================================================================


class TestInitializeCassettes:
    async def test_creates_default_cassettes(self, db_session: AsyncSession) -> None:
        """Initializing an empty DB creates the default $20 cassette with 500 bills."""
        result = await initialize_cassettes(db_session)
        assert len(result) == 1
        assert result[0]["denomination_cents"] == TWENTY_DOLLAR_CENTS
        assert result[0]["bill_count"] == 500
        assert result[0]["max_capacity"] == 2000

    async def test_already_initialized_is_noop(
        self, db_session: AsyncSession
    ) -> None:
        """Calling initialize_cassettes when cassettes already exist does nothing."""
        await _add_cassette(db_session, bill_count=42, max_capacity=100)
        await db_session.commit()

        result = await initialize_cassettes(db_session)
        # Should return current status without adding new cassettes
        assert len(result) == 1
        assert result[0]["bill_count"] == 42
