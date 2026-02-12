"""Seed the database with sample data for development.

Usage:
    python -m scripts.seed_db

Creates the test accounts defined in CLAUDE.md:
    - Alice Johnson: Checking ($5,250) + Savings ($12,500), PIN 1234
    - Bob Williams: Checking ($850.75), PIN 5678
    - Charlie Davis: Checking ($0) + Savings ($100), PIN 9012
"""

import asyncio
import sys

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.atm.config import settings
from src.atm.db.seed import seed_database
from src.atm.models import Base


async def main() -> None:
    """Create tables and seed the database."""
    engine = create_async_engine(settings.database_url, echo=True)

    # Create all tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session, session.begin():
        await seed_database(session)

    await engine.dispose()
    print("Database seeded successfully.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(1)
