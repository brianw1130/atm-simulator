"""Authentication service handling PIN verification, sessions, and lockouts.

Owner: Backend Engineer + Security Engineer
Coverage requirement: 100%

Responsibilities:
    - PIN verification against bcrypt hashes
    - Session creation and validation
    - Failed attempt tracking and account lockout
    - Session timeout enforcement
    - PIN change with complexity validation
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.atm.config import settings
from src.atm.models.account import Account
from src.atm.models.audit import AuditEventType
from src.atm.models.card import ATMCard
from src.atm.services.audit_service import log_event
from src.atm.utils.formatting import mask_account_number
from src.atm.utils.security import (
    generate_session_token,
    hash_pin,
    validate_pin_complexity,
    verify_pin,
)


class AuthenticationError(Exception):
    """Raised when authentication fails."""


class SessionError(Exception):
    """Raised for session-related errors (expired, not found)."""


class PinChangeError(Exception):
    """Raised when a PIN change fails validation."""


@dataclass
class SessionData:
    """In-memory session data for an authenticated user.

    Attributes:
        account_id: The primary account ID associated with this session.
        customer_id: The customer ID who authenticated.
        card_id: The ATM card ID used for authentication.
        created_at: When the session was created.
        last_activity: When the session was last used.
    """

    account_id: int
    customer_id: int
    card_id: int
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# In-memory session store. In production this would be Redis or similar.
_sessions: dict[str, SessionData] = {}


def _get_sessions() -> dict[str, SessionData]:
    """Return the session store. Exists to allow test mocking.

    Returns:
        The global in-memory session dictionary.
    """
    return _sessions


async def authenticate(
    session: AsyncSession,
    card_number: str,
    pin: str,
) -> dict[str, str]:
    """Authenticate a user by card number and PIN.

    Looks up the card, checks for lockout, verifies the PIN, and creates
    a session on success. Tracks failed attempts and locks the card after
    the configured maximum failures.

    Args:
        session: Async SQLAlchemy session for database operations.
        card_number: The ATM card number to authenticate.
        pin: The plaintext PIN entered by the user.

    Returns:
        A dict with keys: session_id, account_number, customer_name, message.

    Raises:
        AuthenticationError: If authentication fails for any reason (invalid
            card, wrong PIN, locked card, inactive card).
    """
    stmt = (
        select(ATMCard)
        .options(
            selectinload(ATMCard.account).selectinload(  # type: ignore[arg-type]
                Account.customer
            )
        )
        .where(ATMCard.card_number == card_number)
    )
    result = await session.execute(stmt)
    card = result.scalars().first()

    if card is None:
        # Use generic message to avoid revealing whether the card exists
        await log_event(
            session,
            AuditEventType.LOGIN_FAILED,
            details={"reason": "card_not_found"},
        )
        raise AuthenticationError("Authentication failed")

    if not card.is_active:
        await log_event(
            session,
            AuditEventType.LOGIN_FAILED,
            account_id=card.account_id,
            details={"reason": "card_inactive"},
        )
        raise AuthenticationError("Authentication failed")

    # Check lockout
    if card.is_locked:
        remaining = card.locked_until - datetime.now(timezone.utc)  # type: ignore[operator]
        remaining_minutes = max(1, int(remaining.total_seconds() / 60))
        await log_event(
            session,
            AuditEventType.LOGIN_FAILED,
            account_id=card.account_id,
            details={"reason": "account_locked", "remaining_minutes": remaining_minutes},
        )
        raise AuthenticationError(
            f"Account is locked. Try again in {remaining_minutes} minute(s)."
        )

    # Verify PIN
    if not verify_pin(pin, card.pin_hash, settings.pin_pepper):
        card.failed_attempts += 1

        if card.failed_attempts >= settings.max_failed_pin_attempts:
            card.locked_until = datetime.now(timezone.utc) + timedelta(
                seconds=settings.lockout_duration_seconds
            )
            await session.flush()
            await log_event(
                session,
                AuditEventType.ACCOUNT_LOCKED,
                account_id=card.account_id,
                details={"failed_attempts": card.failed_attempts},
            )
            raise AuthenticationError(
                "Account locked due to too many failed attempts. "
                f"Try again in {settings.lockout_duration_seconds // 60} minutes."
            )

        await session.flush()
        await log_event(
            session,
            AuditEventType.LOGIN_FAILED,
            account_id=card.account_id,
            details={
                "reason": "invalid_pin",
                "failed_attempts": card.failed_attempts,
            },
        )
        raise AuthenticationError("Authentication failed")

    # Success: reset failed attempts, create session
    card.failed_attempts = 0
    card.locked_until = None
    await session.flush()

    token = generate_session_token()
    sessions = _get_sessions()
    sessions[token] = SessionData(
        account_id=card.account_id,
        customer_id=card.account.customer_id,
        card_id=card.id,
    )

    account = card.account
    customer = account.customer
    masked = mask_account_number(account.account_number)

    await log_event(
        session,
        AuditEventType.LOGIN_SUCCESS,
        account_id=card.account_id,
        session_id=token,
        details={"card_number_last4": card_number[-4:]},
    )

    return {
        "session_id": token,
        "account_number": masked,
        "customer_name": customer.full_name,
        "message": "Authentication successful",
    }


async def validate_session(session_id: str) -> dict[str, int] | None:
    """Validate an active session and refresh its activity timestamp.

    Checks that the session exists and has not exceeded the inactivity
    timeout. Updates the last_activity timestamp on valid sessions.

    Args:
        session_id: The session token to validate.

    Returns:
        A dict with account_id, customer_id, and card_id if the session
        is valid. None if the session is expired or not found.
    """
    sessions = _get_sessions()
    session_data = sessions.get(session_id)
    if session_data is None:
        return None

    now = datetime.now(timezone.utc)
    elapsed = (now - session_data.last_activity).total_seconds()
    if elapsed > settings.session_timeout_seconds:
        # Session expired — remove it
        del sessions[session_id]
        return None

    session_data.last_activity = now
    return {
        "account_id": session_data.account_id,
        "customer_id": session_data.customer_id,
        "card_id": session_data.card_id,
    }


async def logout(
    session: AsyncSession,
    session_id: str,
) -> bool:
    """End an authenticated session.

    Removes the session from the in-memory store and logs the event.

    Args:
        session: Async SQLAlchemy session for audit logging.
        session_id: The session token to invalidate.

    Returns:
        True if the session was found and removed, False if it didn't exist.
    """
    sessions = _get_sessions()
    session_data = sessions.pop(session_id, None)
    if session_data is None:
        return False

    await log_event(
        session,
        AuditEventType.LOGOUT,
        account_id=session_data.account_id,
        session_id=session_id,
    )
    return True


async def change_pin(
    session: AsyncSession,
    session_id: str,
    current_pin: str,
    new_pin: str,
    confirm_pin: str,
) -> dict[str, str]:
    """Change the PIN for the card associated with the current session.

    Validates the current PIN, checks that the new PIN meets complexity
    requirements, and updates the stored hash.

    Args:
        session: Async SQLAlchemy session for database operations.
        session_id: The current session token.
        current_pin: The existing PIN for verification.
        new_pin: The desired new PIN.
        confirm_pin: Confirmation of the new PIN (must match new_pin).

    Returns:
        A dict with a success message.

    Raises:
        SessionError: If the session is invalid or expired.
        PinChangeError: If PIN validation or verification fails.
    """
    session_info = await validate_session(session_id)
    if session_info is None:
        raise SessionError("Session expired or not found")

    card_id = session_info["card_id"]
    account_id = session_info["account_id"]

    # Load the card
    stmt = select(ATMCard).where(ATMCard.id == card_id)
    result = await session.execute(stmt)
    card = result.scalars().first()
    if card is None:
        raise SessionError("Card not found")

    # Verify current PIN
    if not verify_pin(current_pin, card.pin_hash, settings.pin_pepper):
        await log_event(
            session,
            AuditEventType.PIN_CHANGE_FAILED,
            account_id=account_id,
            session_id=session_id,
            details={"reason": "incorrect_current_pin"},
        )
        raise PinChangeError("Current PIN is incorrect")

    # Validate new PIN matches confirmation
    if new_pin != confirm_pin:
        await log_event(
            session,
            AuditEventType.PIN_CHANGE_FAILED,
            account_id=account_id,
            session_id=session_id,
            details={"reason": "confirmation_mismatch"},
        )
        raise PinChangeError("New PIN and confirmation do not match")

    # Check new PIN is different from current
    if verify_pin(new_pin, card.pin_hash, settings.pin_pepper):
        await log_event(
            session,
            AuditEventType.PIN_CHANGE_FAILED,
            account_id=account_id,
            session_id=session_id,
            details={"reason": "same_as_current"},
        )
        raise PinChangeError("New PIN must be different from current PIN")

    # Validate complexity
    is_valid, reason = validate_pin_complexity(new_pin)
    if not is_valid:
        await log_event(
            session,
            AuditEventType.PIN_CHANGE_FAILED,
            account_id=account_id,
            session_id=session_id,
            details={"reason": "complexity_failure", "detail": reason},
        )
        raise PinChangeError(reason)

    # Hash and update
    card.pin_hash = hash_pin(new_pin, settings.pin_pepper)
    await session.flush()

    await log_event(
        session,
        AuditEventType.PIN_CHANGED,
        account_id=account_id,
        session_id=session_id,
    )

    return {"message": "PIN changed successfully"}
