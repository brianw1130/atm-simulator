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
    - get_all_customers: returns customers with account counts, empty DB
    - get_customer_detail: found, not found
    - create_customer: success, duplicate email
    - update_customer: success, not found, duplicate email
    - deactivate_customer: success, not found
    - activate_customer: success, not found
    - create_account: success, customer not found
    - update_account: success, not found
    - close_account: success, non-zero balance, not found
    - admin_reset_pin: success, not found, weak pin
"""

import json

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.atm.config import settings
from src.atm.models.account import Account, AccountStatus, AccountType
from src.atm.models.audit import AuditEventType, AuditLog
from src.atm.services.admin_service import (
    ADMIN_SESSION_PREFIX,
    AdminAuthError,
    activate_customer,
    admin_logout,
    admin_reset_pin,
    authenticate_admin,
    close_account,
    create_account,
    create_admin_user,
    create_customer,
    deactivate_customer,
    export_snapshot,
    freeze_account,
    get_all_accounts,
    get_all_customers,
    get_audit_logs,
    get_customer_detail,
    import_snapshot,
    unfreeze_account,
    update_account,
    update_customer,
    validate_admin_session,
)
from src.atm.services.redis_client import get_redis
from src.atm.utils.security import verify_pin
from tests.factories import create_test_account, create_test_card, create_test_customer

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


# ===========================================================================
# get_all_customers
# ===========================================================================


class TestGetAllCustomers:
    async def test_returns_customers_with_account_counts(self, db_session: AsyncSession) -> None:
        """Returns a list of customer dicts including account_count."""
        customer = await create_test_customer(
            db_session, first_name="Alice", last_name="Johnson", email="alice@test.com"
        )
        await create_test_account(
            db_session, customer_id=customer.id, account_number="1000-0001-0001"
        )
        await create_test_account(
            db_session,
            customer_id=customer.id,
            account_number="1000-0001-0002",
            account_type=AccountType.SAVINGS,
        )
        await db_session.commit()

        customers = await get_all_customers(db_session)
        assert len(customers) == 1
        assert customers[0]["first_name"] == "Alice"
        assert customers[0]["account_count"] == 2
        assert customers[0]["is_active"] is True
        assert customers[0]["date_of_birth"] is not None

    async def test_empty_database_returns_empty_list(self, db_session: AsyncSession) -> None:
        """No customers returns an empty list."""
        customers = await get_all_customers(db_session)
        assert customers == []


# ===========================================================================
# get_customer_detail
# ===========================================================================


class TestGetCustomerDetail:
    async def test_returns_customer_with_accounts_and_cards(self, db_session: AsyncSession) -> None:
        """Returns full customer detail including accounts and cards."""
        customer = await create_test_customer(
            db_session, first_name="Alice", last_name="Johnson", email="alice@test.com"
        )
        account = await create_test_account(
            db_session, customer_id=customer.id, account_number="1000-0001-0001"
        )
        await create_test_card(db_session, account_id=account.id, card_number="1000-0001-0001")
        await db_session.commit()

        detail = await get_customer_detail(db_session, customer.id)
        assert detail is not None
        assert detail["first_name"] == "Alice"
        assert detail["account_count"] == 1
        assert len(detail["accounts"]) == 1
        assert detail["accounts"][0]["account_number"] == "1000-0001-0001"
        assert len(detail["accounts"][0]["cards"]) == 1
        assert detail["accounts"][0]["cards"][0]["card_number"] == "1000-0001-0001"

    async def test_not_found_returns_none(self, db_session: AsyncSession) -> None:
        """Nonexistent customer ID returns None."""
        detail = await get_customer_detail(db_session, 99999)
        assert detail is None


# ===========================================================================
# create_customer
# ===========================================================================


class TestCreateCustomer:
    async def test_creates_customer_successfully(self, db_session: AsyncSession) -> None:
        """Creates a customer and returns the data dict."""
        from datetime import date

        data = {
            "first_name": "New",
            "last_name": "Customer",
            "date_of_birth": date(1985, 3, 20),
            "email": "new@example.com",
            "phone": "555-9999",
        }
        result = await create_customer(db_session, data)
        await db_session.commit()

        assert result["first_name"] == "New"
        assert result["last_name"] == "Customer"
        assert result["email"] == "new@example.com"
        assert result["phone"] == "555-9999"
        assert result["is_active"] is True
        assert result["account_count"] == 0

        # Verify audit log was created
        stmt = select(AuditLog).where(AuditLog.event_type == AuditEventType.CUSTOMER_CREATED)
        log = (await db_session.execute(stmt)).scalars().first()
        assert log is not None
        assert log.details["email"] == "new@example.com"

    async def test_duplicate_email_raises_value_error(self, db_session: AsyncSession) -> None:
        """Creating a customer with an existing email raises ValueError."""
        await create_test_customer(db_session, email="taken@example.com")
        await db_session.commit()

        from datetime import date

        data = {
            "first_name": "Another",
            "last_name": "Person",
            "date_of_birth": date(1990, 1, 1),
            "email": "taken@example.com",
        }
        with pytest.raises(ValueError, match="email already exists"):
            await create_customer(db_session, data)

    async def test_creates_customer_without_phone(self, db_session: AsyncSession) -> None:
        """Creates a customer without an optional phone."""
        from datetime import date

        data = {
            "first_name": "No",
            "last_name": "Phone",
            "date_of_birth": date(1990, 1, 1),
            "email": "nophone@example.com",
        }
        result = await create_customer(db_session, data)
        assert result["phone"] is None


# ===========================================================================
# update_customer
# ===========================================================================


class TestUpdateCustomer:
    async def test_updates_customer_fields(self, db_session: AsyncSession) -> None:
        """Updates specified fields and returns the updated dict."""
        customer = await create_test_customer(
            db_session, first_name="Old", last_name="Name", email="old@example.com"
        )
        await db_session.commit()

        result = await update_customer(
            db_session, customer.id, {"first_name": "New", "last_name": "Name2"}
        )
        assert result is not None
        assert result["first_name"] == "New"
        assert result["last_name"] == "Name2"

    async def test_not_found_returns_none(self, db_session: AsyncSession) -> None:
        """Nonexistent customer ID returns None."""
        result = await update_customer(db_session, 99999, {"first_name": "X"})
        assert result is None

    async def test_duplicate_email_raises_value_error(self, db_session: AsyncSession) -> None:
        """Changing email to one that belongs to another customer raises ValueError."""
        await create_test_customer(db_session, email="taken@example.com")
        customer = await create_test_customer(db_session, email="mine@example.com")
        await db_session.commit()

        with pytest.raises(ValueError, match="email already exists"):
            await update_customer(db_session, customer.id, {"email": "taken@example.com"})

    async def test_same_email_allowed(self, db_session: AsyncSession) -> None:
        """Updating with the same email the customer already has doesn't raise."""
        customer = await create_test_customer(db_session, email="keep@example.com")
        await db_session.commit()

        result = await update_customer(
            db_session, customer.id, {"email": "keep@example.com", "first_name": "Updated"}
        )
        assert result is not None
        assert result["first_name"] == "Updated"

    async def test_audit_log_created(self, db_session: AsyncSession) -> None:
        """Updating a customer creates an audit log entry."""
        customer = await create_test_customer(db_session, email="audit@example.com")
        await db_session.commit()

        await update_customer(db_session, customer.id, {"first_name": "Audited"})
        await db_session.commit()

        stmt = select(AuditLog).where(AuditLog.event_type == AuditEventType.CUSTOMER_UPDATED)
        log = (await db_session.execute(stmt)).scalars().first()
        assert log is not None


# ===========================================================================
# deactivate_customer / activate_customer
# ===========================================================================


class TestDeactivateCustomer:
    async def test_deactivates_customer(self, db_session: AsyncSession) -> None:
        """Sets is_active=False and returns confirmation."""
        customer = await create_test_customer(db_session, first_name="Active")
        await db_session.commit()

        result = await deactivate_customer(db_session, customer.id)
        assert result is not None
        assert "deactivated" in result["message"].lower()

        await db_session.refresh(customer)
        assert customer.is_active is False

    async def test_not_found_returns_none(self, db_session: AsyncSession) -> None:
        """Nonexistent customer ID returns None."""
        result = await deactivate_customer(db_session, 99999)
        assert result is None

    async def test_audit_log_created(self, db_session: AsyncSession) -> None:
        """Deactivating a customer creates an audit log entry."""
        customer = await create_test_customer(db_session)
        await db_session.commit()

        await deactivate_customer(db_session, customer.id)
        await db_session.commit()

        stmt = select(AuditLog).where(AuditLog.event_type == AuditEventType.CUSTOMER_DEACTIVATED)
        log = (await db_session.execute(stmt)).scalars().first()
        assert log is not None


class TestActivateCustomer:
    async def test_activates_customer(self, db_session: AsyncSession) -> None:
        """Sets is_active=True and returns confirmation."""
        customer = await create_test_customer(db_session, is_active=False)
        await db_session.commit()

        result = await activate_customer(db_session, customer.id)
        assert result is not None
        assert "activated" in result["message"].lower()

        await db_session.refresh(customer)
        assert customer.is_active is True

    async def test_not_found_returns_none(self, db_session: AsyncSession) -> None:
        """Nonexistent customer ID returns None."""
        result = await activate_customer(db_session, 99999)
        assert result is None


# ===========================================================================
# create_account
# ===========================================================================


class TestCreateAccount:
    async def test_creates_account_with_card(self, db_session: AsyncSession) -> None:
        """Creates an account and an associated ATM card."""
        customer = await create_test_customer(db_session, email="acct@example.com")
        await db_session.commit()

        data = {"account_type": "CHECKING", "initial_balance_cents": 100_000}
        result = await create_account(db_session, customer.id, data)
        await db_session.commit()

        assert result["account_type"] == "CHECKING"
        assert result["balance"] == "$1,000.00"
        assert result["status"] == "ACTIVE"
        assert len(result["cards"]) == 1
        assert result["account_number"].startswith("1000-")

    async def test_creates_savings_with_zero_balance(self, db_session: AsyncSession) -> None:
        """Creates a savings account with zero initial balance."""
        customer = await create_test_customer(db_session, email="sav@example.com")
        await db_session.commit()

        data = {"account_type": "SAVINGS", "initial_balance_cents": 0}
        result = await create_account(db_session, customer.id, data)
        assert result["account_type"] == "SAVINGS"
        assert result["balance"] == "$0.00"

    async def test_customer_not_found_raises_value_error(self, db_session: AsyncSession) -> None:
        """Creating an account for a nonexistent customer raises ValueError."""
        data = {"account_type": "CHECKING", "initial_balance_cents": 0}
        with pytest.raises(ValueError, match="Customer not found"):
            await create_account(db_session, 99999, data)

    async def test_auto_increments_account_number(self, db_session: AsyncSession) -> None:
        """Second account for the same customer gets an incremented account number."""
        customer = await create_test_customer(db_session, email="multi@example.com")
        await db_session.commit()

        data1 = {"account_type": "CHECKING", "initial_balance_cents": 0}
        result1 = await create_account(db_session, customer.id, data1)
        await db_session.commit()

        data2 = {"account_type": "SAVINGS", "initial_balance_cents": 0}
        result2 = await create_account(db_session, customer.id, data2)

        # Second account should have incremented sequence
        num1 = result1["account_number"]
        num2 = result2["account_number"]
        assert num1 != num2
        # Both should share the customer segment
        assert num1.split("-")[1] == num2.split("-")[1]

    async def test_audit_log_created(self, db_session: AsyncSession) -> None:
        """Creating an account creates an audit log entry."""
        customer = await create_test_customer(db_session, email="audit_acct@example.com")
        await db_session.commit()

        data = {"account_type": "CHECKING", "initial_balance_cents": 50000}
        await create_account(db_session, customer.id, data)
        await db_session.commit()

        stmt = select(AuditLog).where(AuditLog.event_type == AuditEventType.ACCOUNT_CREATED)
        log = (await db_session.execute(stmt)).scalars().first()
        assert log is not None
        assert log.details["initial_balance_cents"] == 50000


# ===========================================================================
# update_account
# ===========================================================================


class TestUpdateAccount:
    async def test_updates_account(self, db_session: AsyncSession) -> None:
        """Updates account and returns dict."""
        customer = await create_test_customer(db_session, email="upd_acct@example.com")
        account = await create_test_account(
            db_session, customer_id=customer.id, account_number="1000-9001-0001"
        )
        await db_session.commit()

        result = await update_account(
            db_session, account.id, {"daily_withdrawal_limit_cents": 100000}
        )
        assert result is not None
        assert result["id"] == account.id

    async def test_not_found_returns_none(self, db_session: AsyncSession) -> None:
        """Nonexistent account ID returns None."""
        result = await update_account(db_session, 99999, {})
        assert result is None


# ===========================================================================
# close_account
# ===========================================================================


class TestCloseAccount:
    async def test_closes_zero_balance_account(self, db_session: AsyncSession) -> None:
        """Closes an account with zero balance."""
        customer = await create_test_customer(db_session, email="close@example.com")
        account = await create_test_account(
            db_session,
            customer_id=customer.id,
            account_number="1000-8001-0001",
            balance_cents=0,
        )
        await db_session.commit()

        result = await close_account(db_session, account.id)
        assert result is not None
        assert "closed" in result["message"].lower()

        stmt = select(Account).where(Account.id == account.id)
        row = (await db_session.execute(stmt)).scalars().first()
        assert row is not None
        assert row.status == AccountStatus.CLOSED

    async def test_non_zero_balance_raises_value_error(self, db_session: AsyncSession) -> None:
        """Cannot close an account with a non-zero balance."""
        customer = await create_test_customer(db_session, email="noclose@example.com")
        account = await create_test_account(
            db_session,
            customer_id=customer.id,
            account_number="1000-8002-0001",
            balance_cents=50000,
        )
        await db_session.commit()

        with pytest.raises(ValueError, match="non-zero balance"):
            await close_account(db_session, account.id)

    async def test_not_found_returns_none(self, db_session: AsyncSession) -> None:
        """Nonexistent account ID returns None."""
        result = await close_account(db_session, 99999)
        assert result is None

    async def test_audit_log_created(self, db_session: AsyncSession) -> None:
        """Closing an account creates an audit log entry."""
        customer = await create_test_customer(db_session, email="closelog@example.com")
        account = await create_test_account(
            db_session,
            customer_id=customer.id,
            account_number="1000-8003-0001",
            balance_cents=0,
        )
        await db_session.commit()

        await close_account(db_session, account.id)
        await db_session.commit()

        stmt = select(AuditLog).where(AuditLog.event_type == AuditEventType.ACCOUNT_CLOSED)
        log = (await db_session.execute(stmt)).scalars().first()
        assert log is not None


# ===========================================================================
# admin_reset_pin
# ===========================================================================


class TestAdminResetPin:
    async def test_resets_pin_successfully(self, db_session: AsyncSession) -> None:
        """Resets the card PIN, clears failed_attempts and locked_until."""
        customer = await create_test_customer(db_session, email="pin@example.com")
        account = await create_test_account(
            db_session,
            customer_id=customer.id,
            account_number="1000-7001-0001",
        )
        card = await create_test_card(
            db_session,
            account_id=account.id,
            card_number="1000-7001-0001",
            pin="5678",
            failed_attempts=3,
        )
        await db_session.commit()

        result = await admin_reset_pin(db_session, card.id, "4829")
        assert result is not None
        assert "reset" in result["message"].lower()

        await db_session.refresh(card)
        assert card.failed_attempts == 0
        assert card.locked_until is None
        assert verify_pin("4829", card.pin_hash, settings.pin_pepper)

    async def test_not_found_returns_none(self, db_session: AsyncSession) -> None:
        """Nonexistent card ID returns None."""
        result = await admin_reset_pin(db_session, 99999, "4829")
        assert result is None

    async def test_weak_pin_raises_value_error(self, db_session: AsyncSession) -> None:
        """A PIN that fails complexity validation raises ValueError."""
        with pytest.raises(ValueError, match="same digit"):
            await admin_reset_pin(db_session, 1, "1111")

    async def test_sequential_pin_raises_value_error(self, db_session: AsyncSession) -> None:
        """A sequential PIN raises ValueError."""
        with pytest.raises(ValueError, match="sequential"):
            await admin_reset_pin(db_session, 1, "1234")

    async def test_audit_log_created(self, db_session: AsyncSession) -> None:
        """Resetting a PIN creates an audit log entry."""
        customer = await create_test_customer(db_session, email="pinlog@example.com")
        account = await create_test_account(
            db_session,
            customer_id=customer.id,
            account_number="1000-7002-0001",
        )
        card = await create_test_card(
            db_session,
            account_id=account.id,
            card_number="1000-7002-0001",
            pin="5678",
        )
        await db_session.commit()

        await admin_reset_pin(db_session, card.id, "4829")
        await db_session.commit()

        stmt = select(AuditLog).where(AuditLog.event_type == AuditEventType.PIN_RESET_ADMIN)
        log = (await db_session.execute(stmt)).scalars().first()
        assert log is not None
        assert log.details["card_id"] == card.id


# ===========================================================================
# export_snapshot
# ===========================================================================


class TestExportSnapshot:
    async def test_exports_correct_structure(self, db_session: AsyncSession) -> None:
        """Snapshot has version, exported_at, customers, and admin_users keys."""
        customer = await create_test_customer(db_session, email="export1@example.com")
        await create_test_account(
            db_session,
            customer_id=customer.id,
            account_number="1000-8001-0001",
        )
        await create_admin_user(db_session, "exportadmin", "pass123")
        await db_session.commit()

        snapshot = await export_snapshot(db_session)

        assert snapshot["version"] == "1.0"
        assert "exported_at" in snapshot
        assert len(snapshot["customers"]) == 1
        assert len(snapshot["admin_users"]) == 1
        assert snapshot["customers"][0]["email"] == "export1@example.com"
        assert snapshot["customers"][0]["accounts"][0]["account_number"] == "1000-8001-0001"

    async def test_empty_database(self, db_session: AsyncSession) -> None:
        """Snapshot from an empty database has empty lists."""
        snapshot = await export_snapshot(db_session)

        assert snapshot["customers"] == []
        assert snapshot["admin_users"] == []

    async def test_pin_sentinel_value(self, db_session: AsyncSession) -> None:
        """Cards export with CHANGE_ME pin sentinel and actual pin_hash."""
        customer = await create_test_customer(db_session, email="exportpin@example.com")
        account = await create_test_account(
            db_session,
            customer_id=customer.id,
            account_number="1000-8002-0001",
        )
        card = await create_test_card(
            db_session,
            account_id=account.id,
            card_number="1000-8002-0001",
            pin="5678",
        )
        await db_session.commit()

        snapshot = await export_snapshot(db_session)
        exported_card = snapshot["customers"][0]["accounts"][0]["cards"][0]

        assert exported_card["pin"] == "CHANGE_ME"
        assert exported_card["pin_hash"] == card.pin_hash
        assert exported_card["card_number"] == "1000-8002-0001"

    async def test_admin_users_included(self, db_session: AsyncSession) -> None:
        """Admin users are exported with CHANGE_ME password sentinel."""
        await create_admin_user(db_session, "adminexport", "secret99")
        await db_session.commit()

        snapshot = await export_snapshot(db_session)

        assert len(snapshot["admin_users"]) == 1
        admin = snapshot["admin_users"][0]
        assert admin["username"] == "adminexport"
        assert admin["password"] == "CHANGE_ME"
        assert "password_hash" in admin

    async def test_audit_log_created(self, db_session: AsyncSession) -> None:
        """Export creates a DATA_EXPORTED audit log entry."""
        await export_snapshot(db_session)
        await db_session.commit()

        stmt = select(AuditLog).where(AuditLog.event_type == AuditEventType.DATA_EXPORTED)
        log = (await db_session.execute(stmt)).scalars().first()
        assert log is not None


# ===========================================================================
# import_snapshot
# ===========================================================================


class TestImportSnapshot:
    async def test_full_import(self, db_session: AsyncSession) -> None:
        """Import a complete snapshot and verify all entities created."""
        snapshot = {
            "version": "1.0",
            "exported_at": "2026-02-14T00:00:00Z",
            "customers": [
                {
                    "first_name": "Test",
                    "last_name": "User",
                    "date_of_birth": "1990-01-01",
                    "email": "import-test@example.com",
                    "phone": "555-9999",
                    "is_active": True,
                    "accounts": [
                        {
                            "account_number": "1000-9001-0001",
                            "account_type": "CHECKING",
                            "balance_cents": 100000,
                            "available_balance_cents": 100000,
                            "status": "ACTIVE",
                            "cards": [
                                {
                                    "card_number": "1000-9001-0001",
                                    "pin": "4826",
                                    "pin_hash": "",
                                    "is_active": True,
                                }
                            ],
                        }
                    ],
                }
            ],
            "admin_users": [
                {
                    "username": "importadmin",
                    "password": "admin456",
                    "role": "admin",
                    "is_active": True,
                }
            ],
        }

        stats = await import_snapshot(db_session, snapshot)
        await db_session.commit()

        assert stats["customers_created"] == 1
        assert stats["accounts_created"] == 1
        assert stats["cards_created"] == 1
        assert stats["admin_users_created"] == 1

        # Verify card PIN was hashed from plaintext
        from src.atm.models.card import ATMCard

        card_result = await db_session.execute(
            select(ATMCard).where(ATMCard.card_number == "1000-9001-0001")
        )
        card = card_result.scalars().first()
        assert card is not None
        assert verify_pin("4826", card.pin_hash, settings.pin_pepper)

    async def test_conflict_skip(self, db_session: AsyncSession) -> None:
        """Skip strategy leaves existing customers unchanged."""
        await create_test_customer(db_session, email="skip@example.com", first_name="Original")
        await db_session.commit()

        snapshot = {
            "version": "1.0",
            "exported_at": "2026-02-14T00:00:00Z",
            "customers": [
                {
                    "first_name": "Replaced",
                    "last_name": "User",
                    "date_of_birth": "1990-01-01",
                    "email": "skip@example.com",
                    "is_active": True,
                    "accounts": [],
                }
            ],
            "admin_users": [],
        }

        stats = await import_snapshot(db_session, snapshot, conflict_strategy="skip")
        assert stats["customers_skipped"] == 1
        assert stats["customers_created"] == 0

    async def test_conflict_replace(self, db_session: AsyncSession) -> None:
        """Replace strategy updates existing customer fields."""
        await create_test_customer(
            db_session, email="replace@example.com", first_name="Original"
        )
        await db_session.commit()

        snapshot = {
            "version": "1.0",
            "exported_at": "2026-02-14T00:00:00Z",
            "customers": [
                {
                    "first_name": "Replaced",
                    "last_name": "User",
                    "date_of_birth": "1990-01-01",
                    "email": "replace@example.com",
                    "is_active": True,
                    "accounts": [],
                }
            ],
            "admin_users": [],
        }

        stats = await import_snapshot(db_session, snapshot, conflict_strategy="replace")
        assert stats["customers_replaced"] == 1

        from src.atm.models.customer import Customer

        cust = (
            await db_session.execute(
                select(Customer).where(Customer.email == "replace@example.com")
            )
        ).scalars().first()
        assert cust is not None
        assert cust.first_name == "Replaced"

    async def test_sentinel_pin_hash_used(self, db_session: AsyncSession) -> None:
        """When pin is CHANGE_ME, the existing pin_hash is used directly."""
        original_hash = "$2b$12$fakehashvalue1234567890abcdefghijklmnopqrstuvwx"
        snapshot = {
            "version": "1.0",
            "exported_at": "2026-02-14T00:00:00Z",
            "customers": [
                {
                    "first_name": "Hash",
                    "last_name": "Test",
                    "date_of_birth": "1990-01-01",
                    "email": "hashtest@example.com",
                    "is_active": True,
                    "accounts": [
                        {
                            "account_number": "1000-9002-0001",
                            "account_type": "SAVINGS",
                            "balance_cents": 50000,
                            "available_balance_cents": 50000,
                            "status": "ACTIVE",
                            "cards": [
                                {
                                    "card_number": "1000-9002-0001",
                                    "pin": "CHANGE_ME",
                                    "pin_hash": original_hash,
                                    "is_active": True,
                                }
                            ],
                        }
                    ],
                }
            ],
            "admin_users": [],
        }

        await import_snapshot(db_session, snapshot)
        await db_session.commit()

        from src.atm.models.card import ATMCard

        card = (
            await db_session.execute(
                select(ATMCard).where(ATMCard.card_number == "1000-9002-0001")
            )
        ).scalars().first()
        assert card is not None
        assert card.pin_hash == original_hash

    async def test_missing_customers_key_raises(self, db_session: AsyncSession) -> None:
        """Snapshot without 'customers' key raises ValueError."""
        with pytest.raises(ValueError, match="missing 'customers'"):
            await import_snapshot(db_session, {"version": "1.0"})

    async def test_missing_version_key_raises(self, db_session: AsyncSession) -> None:
        """Snapshot without 'version' key raises ValueError."""
        with pytest.raises(ValueError, match="missing 'version'"):
            await import_snapshot(db_session, {"customers": []})

    async def test_idempotent_reimport(self, db_session: AsyncSession) -> None:
        """Importing the same snapshot twice with skip strategy is idempotent."""
        snapshot = {
            "version": "1.0",
            "exported_at": "2026-02-14T00:00:00Z",
            "customers": [
                {
                    "first_name": "Idempotent",
                    "last_name": "Test",
                    "date_of_birth": "1990-01-01",
                    "email": "idempotent@example.com",
                    "is_active": True,
                    "accounts": [],
                }
            ],
            "admin_users": [],
        }

        stats1 = await import_snapshot(db_session, snapshot)
        await db_session.commit()
        assert stats1["customers_created"] == 1

        stats2 = await import_snapshot(db_session, snapshot, conflict_strategy="skip")
        assert stats2["customers_skipped"] == 1
        assert stats2["customers_created"] == 0

    async def test_audit_log_created(self, db_session: AsyncSession) -> None:
        """Import creates a DATA_IMPORTED audit log entry."""
        snapshot = {
            "version": "1.0",
            "exported_at": "2026-02-14T00:00:00Z",
            "customers": [],
            "admin_users": [],
        }

        await import_snapshot(db_session, snapshot)
        await db_session.commit()

        stmt = select(AuditLog).where(AuditLog.event_type == AuditEventType.DATA_IMPORTED)
        log = (await db_session.execute(stmt)).scalars().first()
        assert log is not None
        assert log.details["conflict_strategy"] == "skip"

    async def test_daily_counters_reset_on_import(self, db_session: AsyncSession) -> None:
        """Imported accounts have daily usage counters reset to zero."""
        snapshot = {
            "version": "1.0",
            "exported_at": "2026-02-14T00:00:00Z",
            "customers": [
                {
                    "first_name": "Counter",
                    "last_name": "Test",
                    "date_of_birth": "1990-01-01",
                    "email": "counter@example.com",
                    "is_active": True,
                    "accounts": [
                        {
                            "account_number": "1000-9003-0001",
                            "account_type": "CHECKING",
                            "balance_cents": 100000,
                            "available_balance_cents": 100000,
                            "status": "ACTIVE",
                            "cards": [],
                        }
                    ],
                }
            ],
            "admin_users": [],
        }

        await import_snapshot(db_session, snapshot)
        await db_session.commit()

        acct = (
            await db_session.execute(
                select(Account).where(Account.account_number == "1000-9003-0001")
            )
        ).scalars().first()
        assert acct is not None
        assert acct.daily_withdrawal_used_cents == 0
        assert acct.daily_transfer_used_cents == 0


# ===========================================================================
# Round-trip: export → import
# ===========================================================================


class TestExportImportRoundTrip:
    async def test_round_trip(self, db_session: AsyncSession) -> None:
        """Export data, then import into a clean session and verify match."""
        # Seed data
        customer = await create_test_customer(
            db_session, email="roundtrip@example.com", first_name="RT"
        )
        account = await create_test_account(
            db_session,
            customer_id=customer.id,
            account_number="1000-9010-0001",
            balance_cents=300000,
        )
        await create_test_card(
            db_session,
            account_id=account.id,
            card_number="1000-9010-0001",
            pin="5678",
        )
        await create_admin_user(db_session, "rtadmin", "pass123")
        await db_session.commit()

        # Export
        snapshot = await export_snapshot(db_session)
        await db_session.commit()

        assert len(snapshot["customers"]) == 1
        assert snapshot["customers"][0]["email"] == "roundtrip@example.com"
        assert snapshot["customers"][0]["accounts"][0]["balance_cents"] == 300000

        # Re-import with skip (should skip all since data exists)
        stats = await import_snapshot(db_session, snapshot, conflict_strategy="skip")
        assert stats["customers_skipped"] == 1
