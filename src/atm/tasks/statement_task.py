"""Async statement generation Celery task."""

import asyncio
from datetime import date
from typing import Any

from src.atm.worker import celery_app


@celery_app.task(name="generate_statement_async", bind=True)  # type: ignore[untyped-decorator]
def generate_statement_task(
    self: Any,
    account_id: int,
    days: int | None = None,
    start_date_str: str | None = None,
    end_date_str: str | None = None,
) -> dict[str, object]:
    """Generate a PDF statement asynchronously.

    Args:
        self: Celery task instance (bound task).
        account_id: The account to generate the statement for.
        days: Number of days for the statement period.
        start_date_str: Custom start date (ISO format).
        end_date_str: Custom end date (ISO format).

    Returns:
        Statement result dict with file path and metadata.
    """
    from src.atm.db.session import async_session_factory
    from src.atm.services.statement_service import generate_statement

    start_date_val = date.fromisoformat(start_date_str) if start_date_str else None
    end_date_val = date.fromisoformat(end_date_str) if end_date_str else None

    async def _run() -> dict[str, object]:
        async with async_session_factory() as session:
            result = await generate_statement(
                session,
                account_id,
                days=days,
                start_date=start_date_val,
                end_date=end_date_val,
            )
            await session.commit()
            return result

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_run())
    finally:
        loop.close()
