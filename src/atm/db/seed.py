"""Database seeder for development and testing.

Owner: Backend Engineer

Creates sample customers, accounts, and cards as defined in CLAUDE.md:
    - Alice Johnson: Checking ($5,250) + Savings ($12,500), PIN 1234
    - Bob Williams: Checking ($850.75), PIN 5678
    - Charlie Davis: Checking ($0) + Savings ($100), PIN 9012

Supports seeding from a JSON snapshot file when ``snapshot_path`` is provided.
"""

import json
import logging
from datetime import date
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.atm.config import settings
from src.atm.models.account import Account, AccountStatus, AccountType
from src.atm.models.admin import AdminUser
from src.atm.models.card import ATMCard
from src.atm.models.customer import Customer
from src.atm.utils.security import hash_pin

logger = logging.getLogger(__name__)


async def seed_database(
    session: AsyncSession,
    snapshot_path: str | None = None,
) -> None:
    """Populate the database with sample data for development and testing.

    If ``snapshot_path`` is provided and the file exists, seed from the JSON
    snapshot instead of using hardcoded data. Otherwise, fall back to the
    default hardcoded seed data.

    This function is idempotent: it checks for existing data before inserting.
    If any customers already exist, the function returns without making changes.

    Args:
        session: An async SQLAlchemy session. The caller is responsible for
            committing or rolling back the transaction.
        snapshot_path: Optional path to a JSON snapshot file to seed from.
    """
    if snapshot_path:
        path = Path(snapshot_path)
        if path.exists():
            logger.info("Seeding database from snapshot: %s", snapshot_path)
            from src.atm.services.admin_service import import_snapshot

            with open(path) as f:
                data = json.load(f)
            await import_snapshot(session, data, conflict_strategy="skip")
            return
        logger.warning("Snapshot path %s does not exist, falling back to default seed.", path)
    # Seed admin user independently (safe to run on existing databases)
    existing_admin = await session.execute(select(AdminUser).limit(1))
    if existing_admin.scalars().first() is None:
        admin = AdminUser(
            username="admin",
            password_hash=hash_pin("admin123", settings.pin_pepper),
            role="admin",
        )
        session.add(admin)
        await session.flush()

    existing = await session.execute(select(Customer).limit(1))
    if existing.scalars().first() is not None:
        return

    pepper = settings.pin_pepper

    # -- Alice Johnson --
    alice = Customer(
        first_name="Alice",
        last_name="Johnson",
        date_of_birth=date(1990, 5, 15),
        email="alice.johnson@example.com",
        phone="555-0101",
    )
    session.add(alice)
    await session.flush()

    alice_checking = Account(
        customer_id=alice.id,
        account_number="1000-0001-0001",
        account_type=AccountType.CHECKING,
        balance_cents=525_000,
        available_balance_cents=525_000,
        status=AccountStatus.ACTIVE,
    )
    alice_savings = Account(
        customer_id=alice.id,
        account_number="1000-0001-0002",
        account_type=AccountType.SAVINGS,
        balance_cents=1_250_000,
        available_balance_cents=1_250_000,
        status=AccountStatus.ACTIVE,
    )
    session.add_all([alice_checking, alice_savings])
    await session.flush()

    alice_checking_card = ATMCard(
        account_id=alice_checking.id,
        card_number="1000-0001-0001",
        pin_hash=hash_pin("1234", pepper),
    )
    alice_savings_card = ATMCard(
        account_id=alice_savings.id,
        card_number="1000-0001-0002",
        pin_hash=hash_pin("1234", pepper),
    )
    session.add_all([alice_checking_card, alice_savings_card])

    # -- Bob Williams --
    bob = Customer(
        first_name="Bob",
        last_name="Williams",
        date_of_birth=date(1985, 8, 22),
        email="bob.williams@example.com",
        phone="555-0102",
    )
    session.add(bob)
    await session.flush()

    bob_checking = Account(
        customer_id=bob.id,
        account_number="1000-0002-0001",
        account_type=AccountType.CHECKING,
        balance_cents=85_075,
        available_balance_cents=85_075,
        status=AccountStatus.ACTIVE,
    )
    session.add(bob_checking)
    await session.flush()

    bob_checking_card = ATMCard(
        account_id=bob_checking.id,
        card_number="1000-0002-0001",
        pin_hash=hash_pin("5678", pepper),
    )
    session.add(bob_checking_card)

    # -- Charlie Davis --
    charlie = Customer(
        first_name="Charlie",
        last_name="Davis",
        date_of_birth=date(1978, 12, 3),
        email="charlie.davis@example.com",
        phone="555-0103",
    )
    session.add(charlie)
    await session.flush()

    charlie_checking = Account(
        customer_id=charlie.id,
        account_number="1000-0003-0001",
        account_type=AccountType.CHECKING,
        balance_cents=0,
        available_balance_cents=0,
        status=AccountStatus.ACTIVE,
    )
    charlie_savings = Account(
        customer_id=charlie.id,
        account_number="1000-0003-0002",
        account_type=AccountType.SAVINGS,
        balance_cents=10_000,
        available_balance_cents=10_000,
        status=AccountStatus.ACTIVE,
    )
    session.add_all([charlie_checking, charlie_savings])
    await session.flush()

    charlie_checking_card = ATMCard(
        account_id=charlie_checking.id,
        card_number="1000-0003-0001",
        pin_hash=hash_pin("9012", pepper),
    )
    charlie_savings_card = ATMCard(
        account_id=charlie_savings.id,
        card_number="1000-0003-0002",
        pin_hash=hash_pin("9012", pepper),
    )
    session.add_all([charlie_checking_card, charlie_savings_card])

    await session.flush()
