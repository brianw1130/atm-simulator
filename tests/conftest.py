"""Shared test fixtures for the ATM simulator test suite.

Provides:
    - Async test client for FastAPI
    - Test database session (SQLite in-memory)
    - Sample data factories
    - Authenticated session fixtures
"""

import asyncio
import tempfile
from collections.abc import AsyncGenerator

import fakeredis.aioredis
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, selectinload

from src.atm.config import settings
from src.atm.models import Base
from src.atm.models.account import Account
from src.atm.main import app
from src.atm.api import get_db
from src.atm.services.redis_client import set_redis

# Point statement output to a temp directory for tests
settings.statement_output_dir = tempfile.mkdtemp(prefix="atm_statements_")

# The Account.customer relationship defaults to lazy="select" (synchronous),
# which triggers MissingGreenlet errors in async contexts (e.g. statement
# service accessing account.customer). Registering a do_orm_execute event
# on Session automatically adds selectinload(Account.customer) to SELECT
# queries that target Account, so the relationship is eagerly loaded.
@event.listens_for(Session, "do_orm_execute")
def _add_customer_selectinload(orm_execute_state):  # type: ignore[no-untyped-def]
    if not orm_execute_state.is_select:
        return
    # Only add selectinload when Account is among the root entities
    for mapper_entity in orm_execute_state.all_mappers:
        if mapper_entity.class_ is Account:
            orm_execute_state.statement = orm_execute_state.statement.options(
                selectinload(Account.customer)
            )
            break

# Use a unique file-based SQLite for each test run to avoid stale state.
# We use a temp file so parallel runs don't collide.
_test_db_path = tempfile.mktemp(suffix=".db", prefix="atm_test_")
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{_test_db_path}"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_factory = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create all tables before each test and drop them after."""
    # Create a fresh FakeRedis bound to the current event loop.
    # FakeRedis uses internal asyncio.Queue which must be created in the
    # same event loop that will be used for async operations.
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    set_redis(fake)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    # Clear Redis sessions between tests
    await fake.flushall()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a test database session."""
    async with test_session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP test client with test database.

    Overrides the get_db dependency so the FastAPI app uses the test
    database session instead of the production one.
    """

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        try:
            yield db_session
        finally:
            # Always commit so that side-effects (e.g. failed_attempts
            # increments) persist across requests within the same test.
            await db_session.commit()

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
