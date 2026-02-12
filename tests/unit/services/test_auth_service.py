"""Unit tests for auth_service.

Coverage requirement: 100%

Tests:
    - authenticate: valid login, wrong PIN, card not found, inactive card, locked card,
      lockout after max failures
    - validate_session: valid session, expired session, nonexistent session
    - logout: successful logout, nonexistent session
    - change_pin: successful, wrong current PIN, mismatched confirm, same as current,
      complexity failure, expired session, card not found in DB
"""

from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.atm.models.account import Account, AccountStatus, AccountType
from src.atm.models.card import ATMCard
from src.atm.models.customer import Customer
from src.atm.services.auth_service import (
    AuthenticationError,
    PinChangeError,
    SessionData,
    SessionError,
    _get_sessions,
    authenticate,
    change_pin,
    logout,
    validate_session,
)
from src.atm.utils.security import hash_pin

pytestmark = pytest.mark.asyncio

# Must match the pepper in config (settings.pin_pepper)
TEST_PIN = "7856"
TEST_PEPPER = "change-me-in-production"


async def _seed_card(
    db_session: AsyncSession,
    *,
    pin: str = TEST_PIN,
    failed_attempts: int = 0,
    locked_until: datetime | None = None,
    is_active: bool = True,
    card_number: str = "4000-0001-0001",
) -> tuple[Customer, Account, ATMCard]:
    """Seed a customer + account + card with the given PIN."""
    customer = Customer(
        first_name="Alice",
        last_name="Johnson",
        date_of_birth=date(1990, 1, 15),
        email=f"alice-{card_number}@example.com",
    )
    db_session.add(customer)
    await db_session.flush()

    account = Account(
        customer_id=customer.id,
        account_number=f"1000-{card_number[-4:]}",
        account_type=AccountType.CHECKING,
        balance_cents=525_000,
        available_balance_cents=525_000,
        status=AccountStatus.ACTIVE,
    )
    db_session.add(account)
    await db_session.flush()

    pin_hash = hash_pin(pin, TEST_PEPPER)
    card = ATMCard(
        account_id=account.id,
        card_number=card_number,
        pin_hash=pin_hash,
        failed_attempts=failed_attempts,
        locked_until=locked_until,
        is_active=is_active,
    )
    db_session.add(card)
    await db_session.flush()

    return customer, account, card


@pytest.fixture(autouse=True)
def clear_sessions():
    """Clear the in-memory session store before and after each test."""
    sessions = _get_sessions()
    sessions.clear()
    yield
    sessions.clear()


# ── authenticate ─────────────────────────────────────────────────────────────


class TestAuthenticate:
    async def test_successful_login(self, db_session: AsyncSession):
        customer, account, card = await _seed_card(db_session)
        result = await authenticate(db_session, "4000-0001-0001", TEST_PIN)

        assert result["session_id"]
        assert result["customer_name"] == "Alice Johnson"
        assert result["message"] == "Authentication successful"
        assert "****" in result["account_number"]

    async def test_session_created_on_success(self, db_session: AsyncSession):
        await _seed_card(db_session)
        result = await authenticate(db_session, "4000-0001-0001", TEST_PIN)

        sessions = _get_sessions()
        assert result["session_id"] in sessions

    async def test_failed_attempts_reset_on_success(self, db_session: AsyncSession):
        customer, account, card = await _seed_card(db_session, failed_attempts=2)
        await authenticate(db_session, "4000-0001-0001", TEST_PIN)

        await db_session.refresh(card)
        assert card.failed_attempts == 0
        assert card.locked_until is None

    async def test_wrong_pin_raises_auth_error(self, db_session: AsyncSession):
        await _seed_card(db_session)
        with pytest.raises(AuthenticationError, match="Authentication failed"):
            await authenticate(db_session, "4000-0001-0001", "9999")

    async def test_wrong_pin_increments_failed_attempts(self, db_session: AsyncSession):
        customer, account, card = await _seed_card(db_session)
        with pytest.raises(AuthenticationError):
            await authenticate(db_session, "4000-0001-0001", "9999")

        await db_session.refresh(card)
        assert card.failed_attempts == 1

    async def test_card_not_found_raises_auth_error(self, db_session: AsyncSession):
        with pytest.raises(AuthenticationError, match="Authentication failed"):
            await authenticate(db_session, "9999-9999-9999", "1234")

    async def test_inactive_card_raises_auth_error(self, db_session: AsyncSession):
        await _seed_card(db_session, is_active=False)
        with pytest.raises(AuthenticationError, match="Authentication failed"):
            await authenticate(db_session, "4000-0001-0001", TEST_PIN)

    async def test_locked_card_raises_auth_error(self, db_session: AsyncSession):
        # SQLite strips timezone info when selectinload refreshes attributes,
        # making card.locked_until naive. auth_service line 134 subtracts
        # datetime.now(timezone.utc) (aware) from it, causing TypeError.
        # Workaround: patch datetime.now in auth_service to return naive UTC.
        future = datetime.now(timezone.utc) + timedelta(minutes=30)
        await _seed_card(db_session, locked_until=future)

        _real_now = datetime.now

        def _naive_now(tz=None):
            """Return naive UTC datetime to match SQLite-returned values."""
            if tz is not None:
                return _real_now(tz).replace(tzinfo=None)
            return _real_now()

        with patch("src.atm.services.auth_service.datetime", wraps=datetime) as mock_dt:
            mock_dt.now = _naive_now
            with pytest.raises(AuthenticationError, match="Account is locked"):
                await authenticate(db_session, "4000-0001-0001", TEST_PIN)

    async def test_lockout_after_max_failures(self, db_session: AsyncSession):
        customer, account, card = await _seed_card(db_session, failed_attempts=2)

        with pytest.raises(AuthenticationError, match="Account locked"):
            await authenticate(db_session, "4000-0001-0001", "9999")

        await db_session.refresh(card)
        assert card.failed_attempts == 3
        assert card.locked_until is not None


# ── validate_session ─────────────────────────────────────────────────────────


class TestValidateSession:
    async def test_valid_session_returns_data(self, db_session: AsyncSession):
        await _seed_card(db_session)
        result = await authenticate(db_session, "4000-0001-0001", TEST_PIN)
        session_id = result["session_id"]

        info = await validate_session(session_id)
        assert info is not None
        assert "account_id" in info
        assert "customer_id" in info
        assert "card_id" in info

    async def test_nonexistent_session_returns_none(self):
        result = await validate_session("nonexistent-session-token")
        assert result is None

    async def test_expired_session_returns_none(self, db_session: AsyncSession):
        await _seed_card(db_session)
        result = await authenticate(db_session, "4000-0001-0001", TEST_PIN)
        session_id = result["session_id"]

        # Manually expire the session
        sessions = _get_sessions()
        sessions[session_id].last_activity = datetime.now(timezone.utc) - timedelta(minutes=5)

        info = await validate_session(session_id)
        assert info is None

    async def test_expired_session_is_removed(self, db_session: AsyncSession):
        await _seed_card(db_session)
        result = await authenticate(db_session, "4000-0001-0001", TEST_PIN)
        session_id = result["session_id"]

        sessions = _get_sessions()
        sessions[session_id].last_activity = datetime.now(timezone.utc) - timedelta(minutes=5)

        await validate_session(session_id)
        assert session_id not in sessions

    async def test_valid_session_refreshes_activity(self, db_session: AsyncSession):
        await _seed_card(db_session)
        result = await authenticate(db_session, "4000-0001-0001", TEST_PIN)
        session_id = result["session_id"]

        sessions = _get_sessions()
        old_activity = sessions[session_id].last_activity

        import time
        time.sleep(0.01)

        await validate_session(session_id)
        assert sessions[session_id].last_activity >= old_activity


# ── logout ───────────────────────────────────────────────────────────────────


class TestLogout:
    async def test_successful_logout(self, db_session: AsyncSession):
        await _seed_card(db_session)
        result = await authenticate(db_session, "4000-0001-0001", TEST_PIN)
        session_id = result["session_id"]

        success = await logout(db_session, session_id)
        assert success is True

    async def test_session_removed_after_logout(self, db_session: AsyncSession):
        await _seed_card(db_session)
        result = await authenticate(db_session, "4000-0001-0001", TEST_PIN)
        session_id = result["session_id"]

        await logout(db_session, session_id)
        sessions = _get_sessions()
        assert session_id not in sessions

    async def test_logout_nonexistent_session_returns_false(self, db_session: AsyncSession):
        success = await logout(db_session, "nonexistent-session")
        assert success is False


# ── change_pin ───────────────────────────────────────────────────────────────


class TestChangePin:
    async def test_successful_pin_change(self, db_session: AsyncSession):
        customer, account, card = await _seed_card(db_session)
        result = await authenticate(db_session, "4000-0001-0001", TEST_PIN)
        session_id = result["session_id"]

        response = await change_pin(
            db_session, session_id, TEST_PIN, "4829", "4829"
        )
        assert response["message"] == "PIN changed successfully"

    async def test_new_pin_works_after_change(self, db_session: AsyncSession):
        customer, account, card = await _seed_card(db_session)
        result = await authenticate(db_session, "4000-0001-0001", TEST_PIN)
        session_id = result["session_id"]

        await change_pin(db_session, session_id, TEST_PIN, "4829", "4829")

        await logout(db_session, session_id)
        result2 = await authenticate(db_session, "4000-0001-0001", "4829")
        assert result2["session_id"]

    async def test_wrong_current_pin_raises_error(self, db_session: AsyncSession):
        await _seed_card(db_session)
        result = await authenticate(db_session, "4000-0001-0001", TEST_PIN)
        session_id = result["session_id"]

        with pytest.raises(PinChangeError, match="Current PIN is incorrect"):
            await change_pin(db_session, session_id, "9999", "4829", "4829")

    async def test_mismatched_confirm_pin_raises_error(self, db_session: AsyncSession):
        await _seed_card(db_session)
        result = await authenticate(db_session, "4000-0001-0001", TEST_PIN)
        session_id = result["session_id"]

        with pytest.raises(PinChangeError, match="do not match"):
            await change_pin(db_session, session_id, TEST_PIN, "4829", "9999")

    async def test_same_as_current_pin_raises_error(self, db_session: AsyncSession):
        await _seed_card(db_session)
        result = await authenticate(db_session, "4000-0001-0001", TEST_PIN)
        session_id = result["session_id"]

        with pytest.raises(PinChangeError, match="different from current"):
            await change_pin(db_session, session_id, TEST_PIN, TEST_PIN, TEST_PIN)

    async def test_complexity_failure_raises_error(self, db_session: AsyncSession):
        await _seed_card(db_session)
        result = await authenticate(db_session, "4000-0001-0001", TEST_PIN)
        session_id = result["session_id"]

        with pytest.raises(PinChangeError, match="same digit"):
            await change_pin(db_session, session_id, TEST_PIN, "1111", "1111")

    async def test_expired_session_raises_session_error(self, db_session: AsyncSession):
        await _seed_card(db_session)
        result = await authenticate(db_session, "4000-0001-0001", TEST_PIN)
        session_id = result["session_id"]

        sessions = _get_sessions()
        sessions[session_id].last_activity = datetime.now(timezone.utc) - timedelta(minutes=5)

        with pytest.raises(SessionError, match="expired"):
            await change_pin(db_session, session_id, TEST_PIN, "4829", "4829")

    async def test_nonexistent_session_raises_session_error(self, db_session: AsyncSession):
        with pytest.raises(SessionError, match="expired"):
            await change_pin(
                db_session, "nonexistent-session", TEST_PIN, "4829", "4829"
            )

    async def test_card_not_found_raises_session_error(self, db_session: AsyncSession):
        sessions = _get_sessions()
        sessions["fake-session"] = SessionData(
            account_id=999,
            customer_id=999,
            card_id=999,
        )

        with pytest.raises(SessionError, match="Card not found"):
            await change_pin(
                db_session, "fake-session", TEST_PIN, "4829", "4829"
            )
