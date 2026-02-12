"""Statement generation API endpoints.

Owner: Backend Engineer
Depends on: statement_service, statement schemas

Routes:
    POST /generate — Generate PDF statement for date range
"""

from fastapi import APIRouter, Header, HTTPException, status
from typing import Annotated

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
