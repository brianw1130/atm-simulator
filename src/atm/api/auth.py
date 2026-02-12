"""Authentication API endpoints.

Owner: Backend Engineer
Depends on: auth_service, auth schemas

Routes:
    POST /login — Authenticate with card number + PIN
    POST /logout — End the current session
    POST /pin/change — Change the PIN (requires active session)
"""

from fastapi import APIRouter, Header, HTTPException, status
from typing import Annotated

from src.atm.api import CurrentSession, DbSession
from src.atm.schemas.auth import (
    LoginRequest,
    LoginResponse,
    PinChangeRequest,
    PinChangeResponse,
)
from src.atm.schemas.transaction import ErrorResponse
from src.atm.services.auth_service import (
    AuthenticationError,
    PinChangeError,
    SessionError,
    authenticate,
    change_pin,
    logout,
)

router = APIRouter()


@router.post(
    "/login",
    response_model=LoginResponse,
    responses={401: {"model": ErrorResponse}},
)
async def login(body: LoginRequest, db: DbSession) -> LoginResponse:
    """Authenticate with card number and PIN.

    Args:
        body: Login request containing card_number and pin.
        db: Database session dependency.

    Returns:
        Login response with session token and account details.
    """
    try:
        result = await authenticate(db, body.card_number, body.pin)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    return LoginResponse(**result)


@router.post("/logout")
async def logout_endpoint(
    db: DbSession,
    session_info: CurrentSession,
    x_session_id: Annotated[str, Header()],
) -> dict[str, str]:
    """End the current authenticated session.

    Args:
        db: Database session dependency.
        session_info: Validated session data from dependency.
        x_session_id: Session token from request header.

    Returns:
        Success message.
    """
    await logout(db, x_session_id)
    return {"message": "Logged out successfully"}


@router.post(
    "/pin/change",
    response_model=PinChangeResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
    },
)
async def pin_change(
    body: PinChangeRequest,
    db: DbSession,
    session_info: CurrentSession,
    x_session_id: Annotated[str, Header()],
) -> PinChangeResponse:
    """Change the PIN for the authenticated card.

    Args:
        body: PIN change request with current, new, and confirmation PINs.
        db: Database session dependency.
        session_info: Validated session data from dependency.
        x_session_id: Session token from request header.

    Returns:
        Success message confirming PIN change.
    """
    try:
        result = await change_pin(
            db,
            x_session_id,
            body.current_pin,
            body.new_pin,
            body.confirm_pin,
        )
    except SessionError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    except PinChangeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return PinChangeResponse(**result)
