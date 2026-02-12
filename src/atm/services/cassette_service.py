"""Cash cassette service for managing ATM bill inventory."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.atm.models.cassette import CashCassette

TWENTY_DOLLAR_CENTS = 2_000


async def get_cassette_status(session: AsyncSession) -> list[dict]:
    """Get current bill counts for all denominations.

    Args:
        session: Async SQLAlchemy session.

    Returns:
        List of dicts with denomination_cents, bill_count, max_capacity,
        and total_value_cents for each cassette.
    """
    stmt = select(CashCassette).order_by(CashCassette.denomination_cents)
    result = await session.execute(stmt)
    cassettes = result.scalars().all()
    return [
        {
            "denomination_cents": c.denomination_cents,
            "bill_count": c.bill_count,
            "max_capacity": c.max_capacity,
            "total_value_cents": c.denomination_cents * c.bill_count,
        }
        for c in cassettes
    ]


async def can_dispense(session: AsyncSession, amount_cents: int) -> bool:
    """Check if the ATM can dispense the requested amount.

    If no cassettes exist in the database, returns True (backward compatibility).
    Currently only supports $20 bills.

    Args:
        session: Async SQLAlchemy session.
        amount_cents: Amount to dispense in cents.

    Returns:
        True if the ATM has enough bills to dispense the amount.
    """
    stmt = select(CashCassette).where(
        CashCassette.denomination_cents == TWENTY_DOLLAR_CENTS
    )
    result = await session.execute(stmt)
    cassette = result.scalars().first()

    if cassette is None:
        # No cassettes configured — unlimited bills (backward compat)
        return True

    bills_needed = amount_cents // TWENTY_DOLLAR_CENTS
    return cassette.bill_count >= bills_needed


async def dispense_bills(session: AsyncSession, amount_cents: int) -> dict:
    """Dispense bills and deduct from cassette inventory.

    If no cassettes exist, returns the denomination breakdown without
    tracking (backward compatibility).

    Args:
        session: Async SQLAlchemy session.
        amount_cents: Amount to dispense in cents.

    Returns:
        Dict with denomination breakdown (twenties, total_bills, total_amount).
    """
    bills_needed = amount_cents // TWENTY_DOLLAR_CENTS

    stmt = select(CashCassette).where(
        CashCassette.denomination_cents == TWENTY_DOLLAR_CENTS
    )
    result = await session.execute(stmt)
    cassette = result.scalars().first()

    if cassette is not None:
        cassette.bill_count -= bills_needed
        await session.flush()

    return {
        "twenties": bills_needed,
        "total_bills": bills_needed,
        "total_amount": f"${amount_cents / 100:,.2f}",
    }


async def refill_cassette(
    session: AsyncSession,
    denomination_cents: int,
    bill_count: int,
) -> dict:
    """Add bills to a cassette (admin operation).

    Args:
        session: Async SQLAlchemy session.
        denomination_cents: The denomination in cents (e.g., 2000 for $20).
        bill_count: Number of bills to add.

    Returns:
        Dict with the cassette's denomination_cents, bill_count, and max_capacity.
    """
    stmt = select(CashCassette).where(
        CashCassette.denomination_cents == denomination_cents
    )
    result = await session.execute(stmt)
    cassette = result.scalars().first()

    if cassette is None:
        cassette = CashCassette(
            denomination_cents=denomination_cents,
            bill_count=bill_count,
            last_refilled_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        session.add(cassette)
    else:
        cassette.bill_count = min(
            cassette.bill_count + bill_count,
            cassette.max_capacity,
        )
        cassette.last_refilled_at = datetime.now(timezone.utc).replace(tzinfo=None)

    await session.flush()
    return {
        "denomination_cents": cassette.denomination_cents,
        "bill_count": cassette.bill_count,
        "max_capacity": cassette.max_capacity,
    }


async def initialize_cassettes(session: AsyncSession) -> list[dict]:
    """Seed default cassettes (500 x $20 bills = $10,000).

    If cassettes already exist, returns the current status without changes.

    Args:
        session: Async SQLAlchemy session.

    Returns:
        List of cassette status dicts.
    """
    # Check if already initialized
    stmt = select(CashCassette)
    result = await session.execute(stmt)
    existing = result.scalars().first()
    if existing is not None:
        return await get_cassette_status(session)

    cassette = CashCassette(
        denomination_cents=TWENTY_DOLLAR_CENTS,
        bill_count=500,
        max_capacity=2000,
        last_refilled_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    session.add(cassette)
    await session.flush()
    return await get_cassette_status(session)
