"""FastAPI route handlers for the ATM API."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.atm.db.session import async_session_factory
from src.atm.services.auth_service import validate_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional database session for a single request.

    Yields:
        An async SQLAlchemy session. Commits on success, rolls back on error.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_current_session(
    x_session_id: Annotated[str, Header()],
) -> dict[str, int]:
    """FastAPI dependency that validates the session token from the X-Session-ID header.

    Args:
        x_session_id: Session token from the request header.

    Returns:
        A dict with account_id, customer_id, and card_id.

    Raises:
        HTTPException: 401 if the session is invalid or expired.
    """
    session_data = await validate_session(x_session_id)
    if session_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session is invalid or expired",
        )
    return session_data


DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentSession = Annotated[dict[str, int], Depends(get_current_session)]
