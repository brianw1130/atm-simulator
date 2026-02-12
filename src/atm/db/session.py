"""Async SQLAlchemy session factory and dependency injection.

Owner: Backend Engineer

Provides:
    - get_async_session: FastAPI dependency for request-scoped DB sessions
    - async_engine: Shared async engine instance
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.atm.config import settings

async_engine = create_async_engine(
    settings.database_url,
    echo=settings.is_development,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncSession:  # type: ignore[misc]
    """FastAPI dependency that provides a database session.

    Yields:
        An async SQLAlchemy session that is automatically closed after use.
    """
    async with async_session_factory() as session:
        yield session
