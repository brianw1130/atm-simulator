"""Unit tests for seed_database with snapshot support."""

import json
import tempfile

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.atm.db.seed import seed_database
from src.atm.models.customer import Customer

pytestmark = pytest.mark.asyncio


class TestSeedFromSnapshot:
    async def test_seed_from_snapshot_file(self, db_session: AsyncSession) -> None:
        """Seeding from a valid snapshot file creates entities."""
        snapshot = {
            "version": "1.0",
            "exported_at": "2026-02-14T00:00:00Z",
            "customers": [
                {
                    "first_name": "Snapshot",
                    "last_name": "User",
                    "date_of_birth": "1990-01-01",
                    "email": "snapshot-seed@example.com",
                    "is_active": True,
                    "accounts": [],
                }
            ],
            "admin_users": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(snapshot, f)
            path = f.name

        await seed_database(db_session, snapshot_path=path)
        await db_session.commit()

        result = await db_session.execute(
            select(Customer).where(Customer.email == "snapshot-seed@example.com")
        )
        customer = result.scalars().first()
        assert customer is not None
        assert customer.first_name == "Snapshot"

    async def test_seed_missing_file_falls_back(self, db_session: AsyncSession) -> None:
        """A nonexistent snapshot path falls back to default seeding."""
        await seed_database(db_session, snapshot_path="/nonexistent/path/snapshot.json")
        await db_session.commit()

        # Default seed creates Alice Johnson
        result = await db_session.execute(
            select(Customer).where(Customer.email == "alice.johnson@example.com")
        )
        customer = result.scalars().first()
        assert customer is not None

    async def test_seed_no_snapshot_uses_defaults(self, db_session: AsyncSession) -> None:
        """No snapshot path uses the default hardcoded seed data."""
        await seed_database(db_session)
        await db_session.commit()

        result = await db_session.execute(select(Customer))
        customers = result.scalars().all()
        assert len(customers) == 3  # Alice, Bob, Charlie

    async def test_seed_idempotent(self, db_session: AsyncSession) -> None:
        """Running seed twice doesn't duplicate data."""
        await seed_database(db_session)
        await db_session.commit()

        await seed_database(db_session)
        await db_session.commit()

        result = await db_session.execute(select(Customer))
        customers = result.scalars().all()
        assert len(customers) == 3
