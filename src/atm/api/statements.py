"""Statement generation API endpoints.

Owner: Backend Engineer
Depends on: statement_service, statement schemas

Routes:
    POST /generate — Generate PDF statement for date range
    POST /generate-async — Queue async PDF statement generation
    GET /status/{task_id} — Check async statement generation status
"""

from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, status

from src.atm.api import CurrentSession, DbSession
from src.atm.schemas.transaction import (
    ErrorResponse,
    StatementRequest,
    StatementResponse,
)
from src.atm.services.statement_service import (
    StatementError,
    generate_statement,
)

router = APIRouter()


@router.post(
    "/generate",
    response_model=StatementResponse,
    responses={
        400: {"model": ErrorResponse},
    },
)
async def generate_statement_endpoint(
    body: StatementRequest,
    db: DbSession,
    session_info: CurrentSession,
    x_session_id: Annotated[str, Header()],
) -> StatementResponse:
    """Generate a PDF account statement for a date range.

    Args:
        body: Statement request with days or custom date range.
        db: Database session dependency.
        session_info: Validated session data from dependency.
        x_session_id: Session token for audit logging.

    Returns:
        Statement metadata including file path and period details.
    """
    try:
        result = await generate_statement(
            db,
            session_info["account_id"],
            days=body.days if body.start_date is None else None,
            start_date=body.start_date,
            end_date=body.end_date,
            session_id=x_session_id,
        )
    except StatementError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return StatementResponse(**result)


@router.post(
    "/generate-async",
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_statement_async_endpoint(
    body: StatementRequest,
    session_info: CurrentSession,
    x_session_id: Annotated[str, Header()],
) -> dict[str, str]:
    """Queue async PDF statement generation.

    Returns 202 with a task_id that can be polled via the status endpoint.

    Args:
        body: Statement request with days or custom date range.
        session_info: Validated session data from dependency.
        x_session_id: Session token for audit logging.

    Returns:
        Dict with task_id and status.
    """
    from src.atm.tasks.statement_task import generate_statement_task

    task = generate_statement_task.delay(
        account_id=session_info["account_id"],
        days=body.days if body.start_date is None else None,
        start_date_str=str(body.start_date) if body.start_date else None,
        end_date_str=str(body.end_date) if body.end_date else None,
    )
    return {"task_id": task.id, "status": "processing"}


@router.get("/status/{task_id}")
async def get_statement_status(
    task_id: str,
    session_info: CurrentSession,
) -> dict[str, object]:
    """Check the status of an async statement generation task.

    Args:
        task_id: The Celery task ID to check.
        session_info: Validated session data from dependency.

    Returns:
        Dict with task_id, status, and optionally result or error.
    """
    from celery.result import AsyncResult

    result = AsyncResult(task_id)

    if result.state == "PENDING":
        return {"task_id": task_id, "status": "pending"}
    elif result.state == "STARTED":
        return {"task_id": task_id, "status": "processing"}
    elif result.state == "SUCCESS":
        return {"task_id": task_id, "status": "completed", "result": result.result}
    elif result.state == "FAILURE":
        return {"task_id": task_id, "status": "failed", "error": str(result.result)}
    else:
        return {"task_id": task_id, "status": result.state.lower()}
