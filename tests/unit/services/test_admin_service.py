"""Unit tests for admin_service.

Coverage requirement: 100%

Tests:
    - authenticate_admin: valid login, invalid password, nonexistent user, inactive user
    - validate_admin_session: valid token, expired/missing token, TTL refresh
    - admin_logout: valid session, already-expired session
    - get_all_accounts: returns accounts with customer info, empty DB
    - freeze_account: success, account not found
    - unfreeze_account: success, account not found
    - get_audit_logs: returns logs, filter by event_type, empty
    - create_admin_user: success, creates with hashed password
"""

import json

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.atm.config import settings
from src.atm.models.account import Account, AccountStatus, AccountType
from src.atm.models.audit import AuditEventType, AuditLog
from src.atm.services.admin_service import (
    ADMIN_SESSION_PREFIX,
    AdminAuthError,
    admin_logout,
    authenticate_admin,
    create_admin_user,
    freeze_account,
    get_all_accounts,
    get_audit_logs,
    unfreeze_account,
    validate_admin_session,
)
from src.atm.services.redis_client import get_redis
from src.atm.utils.security import verify_pin
from tests.factories import create_test_account, create_test_customer

pytestmark = pytest.mark.asyncio

TEST_ADMIN_USERNAME = "testadmin"
TEST_ADMIN_PASSWORD = "securepass99"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_admin(db_session: AsyncSession, *, is_active: bool = True) -> None:
    """Create a test admin user in the database."""
    admin = await create_admin_user(db_session, TEST_ADMIN_USERNAME, TEST_ADMIN_PASSWORD)
    if not is_active:
        admin.is_active = False
        await db_session.flush()
    await db_session.commit()


async def _seed_accounts(db_session: AsyncSession) -> tuple[int, int]:
    """Seed two accounts (checking + savings) for testing. Return their IDs."""
    customer = await create_test_customer(db_session, first_name="Alice", last_name="Johnson")
    checking = await create_test_account(
        db_session,
        customer_id=customer.id,
        account_number="1000-0001-0001",
        account_type=AccountType.CHECKING,
        balance_cents=525_000,
    )
    savings = await create_test_account(
        db_session,
        customer_id=customer.id,
        account_number="1000-0001-0002",
        account_type=AccountType.SAVINGS,
        balance_cents=1_250_000,
    )
    await db_session.commit()
    return checking.id, savings.id


# ===========================================================================
# authenticate_admin
# ===========================================================================


class TestAuthenticateAdmin:
    async def test_valid_login_returns_token(self, db_session: AsyncSession) -> None:
        """A valid username/password pair returns a session token string."""
        await _create_admin(db_session)
        token = await authenticate_admin(db_session, TEST_ADMIN_USERNAME, TEST_ADMIN_PASSWORD)

        assert isinstance(token, str)
        assert len(token) > 0

        # Verify the token is stored in Redis
        redis = await get_redis()
        data = await redis.get(f"{ADMIN_SESSION_PREFIX}{token}")
        assert data is not None
        session_data = json.loads(data)
        assert session_data["username"] == TEST_ADMIN_USERNAME
        assert session_data["role"] == "admin"

    async def test_invalid_password_raises_auth_error(self, db_session: AsyncSession) -> None:
        """Wrong password raises AdminAuthError."""
        await _create_admin(db_session)
        with pytest.raises(AdminAuthError, match="Invalid credentials"):
            await authenticate_admin(db_session, TEST_ADMIN_USERNAME, "wrongpass")

    async def test_nonexistent_user_raises_auth_error(self, db_session: AsyncSession) -> None:
        """A username that does not exist raises AdminAuthError."""
        with pytest.raises(AdminAuthError, match="Invalid credentials"):
            await authenticate_admin(db_session, "nobody", "anypass")

    async def test_inactive_user_raises_auth_error(self, db_session: AsyncSession) -> None:
        """An inactive admin user cannot authenticate."""
        await _create_admin(db_session, is_active=False)
        with pytest.raises(AdminAuthError, match="Invalid credentials"):
            await authenticate_admin(db_session, TEST_ADMIN_USERNAME, TEST_ADMIN_PASSWORD)


# ===========================================================================
# validate_admin_session
# ===========================================================================


class TestValidateAdminSession:
    async def test_valid_token_returns_session_data(self, db_session: AsyncSession) -> None:
        """A valid token returns the stored admin session dict."""
        await _create_admin(db_session)
        token = await authenticate_admin(db_session, TEST_ADMIN_USERNAME, TEST_ADMIN_PASSWORD)

        data = await validate_admin_session(token)
        assert data is not None
        assert data["username"] == TEST_ADMIN_USERNAME
        assert "admin_id" in data

    async def test_expired_or_missing_token_returns_none(self, db_session: AsyncSession) -> None:
        """An invalid/missing token returns None."""
        result = await validate_admin_session("nonexistent-token-abc")
        assert result is None

    async def test_ttl_refreshed_on_validation(self, db_session: AsyncSession) -> None:
        """Validating a session refreshes its TTL in Redis."""
        await _create_admin(db_session)
        token = await authenticate_admin(db_session, TEST_ADMIN_USERNAME, TEST_ADMIN_PASSWORD)

        redis = await get_redis()
        key = f"{ADMIN_SESSION_PREFIX}{token}"

        # Manually reduce TTL to a low value
        await redis.expire(key, 10)
        ttl_before = await redis.ttl(key)
        assert ttl_before <= 10

        # validate_admin_session should refresh it
        await validate_admin_session(token)
        ttl_after = await redis.ttl(key)
        assert ttl_after > 10  # Refreshed to ADMIN_SESSION_TTL


# ===========================================================================
# admin_logout
# ===========================================================================


class TestAdminLogout:
    async def test_valid_session_returns_true(self, db_session: AsyncSession) -> None:
        """Logging out an existing session returns True and removes the key."""
        await _create_admin(db_session)
        token = await authenticate_admin(db_session, TEST_ADMIN_USERNAME, TEST_ADMIN_PASSWORD)

        result = await admin_logout(token)
        assert result is True

        # Key should be gone
        redis = await get_redis()
        data = await redis.get(f"{ADMIN_SESSION_PREFIX}{token}")
        assert data is None

    async def test_already_expired_session_returns_false(self, db_session: AsyncSession) -> None:
        """Logging out a non-existent session returns False."""
        result = await admin_logout("nonexistent-token-xyz")
        assert result is False


# ===========================================================================
# get_all_accounts
# ===========================================================================


class TestGetAllAccounts:
    async def test_returns_accounts_with_customer_info(self, db_session: AsyncSession) -> None:
        """Returns a list of account dicts including customer name and balance."""
        await _seed_accounts(db_session)
        accounts = await get_all_accounts(db_session)

        assert len(accounts) == 2
        checking = accounts[0]
        assert checking["account_number"] == "1000-0001-0001"
        assert checking["account_type"] == "CHECKING"
        assert checking["balance"] == "$5,250.00"
        assert checking["status"] == "ACTIVE"
        assert checking["customer_name"] == "Alice Johnson"

    async def test_empty_database_returns_empty_list(self, db_session: AsyncSession) -> None:
        """No accounts in the DB returns an empty list."""
        accounts = await get_all_accounts(db_session)
        assert accounts == []


# ===========================================================================
# freeze_account / unfreeze_account
# ===========================================================================


class TestFreezeAccount:
    async def test_freeze_success(self, db_session: AsyncSession) -> None:
        """Freezing an active account sets its status to FROZEN."""
        checking_id, _ = await _seed_accounts(db_session)
        result = await freeze_account(db_session, checking_id)

        assert "frozen" in result["message"].lower()

        from sqlalchemy import select

        stmt = select(Account).where(Account.id == checking_id)
        row = (await db_session.execute(stmt)).scalars().first()
        assert row is not None
        assert row.status == AccountStatus.FROZEN

    async def test_freeze_account_not_found(self, db_session: AsyncSession) -> None:
        """Freezing a nonexistent account raises ValueError."""
        with pytest.raises(ValueError, match="Account not found"):
            await freeze_account(db_session, 99999)


class TestUnfreezeAccount:
    async def test_unfreeze_success(self, db_session: AsyncSession) -> None:
        """Unfreezing a frozen account restores it to ACTIVE."""
        checking_id, _ = await _seed_accounts(db_session)
        # First freeze, then unfreeze
        await freeze_account(db_session, checking_id)
        result = await unfreeze_account(db_session, checking_id)

        assert "unfrozen" in result["message"].lower()

        from sqlalchemy import select

        stmt = select(Account).where(Account.id == checking_id)
        row = (await db_session.execute(stmt)).scalars().first()
        assert row is not None
        assert row.status == AccountStatus.ACTIVE

    async def test_unfreeze_account_not_found(self, db_session: AsyncSession) -> None:
        """Unfreezing a nonexistent account raises ValueError."""
        with pytest.raises(ValueError, match="Account not found"):
            await unfreeze_account(db_session, 99999)


# ===========================================================================
# get_audit_logs
# ===========================================================================


class TestGetAuditLogs:
    async def _seed_logs(self, db_session: AsyncSession) -> None:
        """Create a few audit log entries."""
        for i in range(3):
            log = AuditLog(
                event_type=AuditEventType.LOGIN_SUCCESS,
                details={"attempt": i},
            )
            db_session.add(log)
        log_fail = AuditLog(
            event_type=AuditEventType.LOGIN_FAILED,
            details={"reason": "wrong PIN"},
        )
        db_session.add(log_fail)
        await db_session.flush()
        await db_session.commit()

    async def test_returns_logs(self, db_session: AsyncSession) -> None:
        """Returns all audit logs when no filter is applied."""
        await self._seed_logs(db_session)
        logs = await get_audit_logs(db_session)

        assert len(logs) == 4
        for log in logs:
            assert "id" in log
            assert "event_type" in log
            assert "created_at" in log

    async def test_filter_by_event_type(self, db_session: AsyncSession) -> None:
        """Filtering by event_type returns only matching entries."""
        await self._seed_logs(db_session)
        logs = await get_audit_logs(db_session, event_type="LOGIN_FAILED")

        assert len(logs) == 1
        assert logs[0]["event_type"] == "LOGIN_FAILED"

    async def test_empty_logs(self, db_session: AsyncSession) -> None:
        """No audit logs returns an empty list."""
        logs = await get_audit_logs(db_session)
        assert logs == []


# ===========================================================================
# create_admin_user
# ===========================================================================


class TestCreateAdminUser:
    async def test_creates_admin_with_hashed_password(self, db_session: AsyncSession) -> None:
        """create_admin_user stores a bcrypt-hashed password, not plaintext."""
        admin = await create_admin_user(db_session, "newadmin", "mypassword123")
        await db_session.commit()

        assert admin.username == "newadmin"
        assert admin.role == "admin"
        assert admin.is_active is True
        # Password hash should NOT be the plaintext password
        assert admin.password_hash != "mypassword123"
        # But it should verify correctly
        assert verify_pin("mypassword123", admin.password_hash, settings.pin_pepper)

    async def test_creates_admin_with_custom_role(self, db_session: AsyncSession) -> None:
        """create_admin_user accepts a custom role."""
        admin = await create_admin_user(db_session, "superadmin", "pass456", role="superadmin")
        await db_session.commit()

        assert admin.role == "superadmin"
