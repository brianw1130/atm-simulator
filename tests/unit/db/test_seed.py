"""Unit tests for seed_database with snapshot support."""

import json
import tempfile
from unittest.mock import patch

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


class TestSeedFromS3:
    async def test_seed_from_s3_key(self, db_session: AsyncSession) -> None:
        """Seeding from a valid S3 snapshot key imports entities."""
        s3_snapshot = {
            "version": "1.0",
            "exported_at": "2026-02-14T00:00:00Z",
            "customers": [
                {
                    "first_name": "S3Seed",
                    "last_name": "User",
                    "date_of_birth": "1990-01-01",
                    "email": "s3-seed@example.com",
                    "is_active": True,
                    "accounts": [],
                }
            ],
            "admin_users": [],
        }

        with (
            patch("src.atm.db.seed.settings") as mock_settings,
            patch(
                "src.atm.services.s3_client.download_snapshot", return_value=s3_snapshot
            ) as mock_dl,
        ):
            mock_settings.seed_snapshot_s3_key = "snapshots/test.json"
            mock_settings.seed_snapshot_path = ""
            mock_settings.pin_pepper = "test-pepper"
            await seed_database(db_session)
            await db_session.commit()

            mock_dl.assert_called_once_with("snapshots/test.json")

        result = await db_session.execute(
            select(Customer).where(Customer.email == "s3-seed@example.com")
        )
        customer = result.scalars().first()
        assert customer is not None
        assert customer.first_name == "S3Seed"

    async def test_seed_s3_download_failure_falls_back(self, db_session: AsyncSession) -> None:
        """When S3 download returns None, seed falls back to hardcoded defaults."""
        with (
            patch("src.atm.db.seed.settings") as mock_settings,
            patch("src.atm.services.s3_client.download_snapshot", return_value=None),
        ):
            mock_settings.seed_snapshot_s3_key = "snapshots/missing.json"
            mock_settings.seed_snapshot_path = ""
            mock_settings.pin_pepper = "test-pepper"
            await seed_database(db_session)
            await db_session.commit()

        # Should have fallen back to default seed (Alice, Bob, Charlie)
        result = await db_session.execute(
            select(Customer).where(Customer.email == "alice.johnson@example.com")
        )
        customer = result.scalars().first()
        assert customer is not None
