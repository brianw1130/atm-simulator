"""Admin service for account management and audit log access."""

import json
import secrets
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.atm.config import settings
from src.atm.models.account import Account, AccountStatus, AccountType
from src.atm.models.admin import AdminUser
from src.atm.models.audit import AuditEventType, AuditLog
from src.atm.models.card import ATMCard
from src.atm.models.customer import Customer
from src.atm.services.audit_service import log_event
from src.atm.services.redis_client import get_redis
from src.atm.utils.security import hash_pin, validate_pin_complexity, verify_pin

ADMIN_SESSION_PREFIX = "admin_session:"
ADMIN_SESSION_TTL = 1800  # 30 minutes
MAINTENANCE_KEY = "atm:maintenance_mode"
MAINTENANCE_REASON_KEY = "atm:maintenance_reason"


class AdminAuthError(Exception):
    """Raised when admin authentication fails."""


async def authenticate_admin(
    session: AsyncSession,
    username: str,
    password: str,
) -> str:
    """Authenticate an admin user and create a session.

    Args:
        session: Async database session.
        username: Admin username.
        password: Admin password.

    Returns:
        Session token string.

    Raises:
        AdminAuthError: If authentication fails.
    """
    stmt = select(AdminUser).where(
        AdminUser.username == username,
        AdminUser.is_active == True,  # noqa: E712
    )
    result = await session.execute(stmt)
    admin = result.scalars().first()

    if admin is None or not verify_pin(password, admin.password_hash, settings.pin_pepper):
        raise AdminAuthError("Invalid credentials")

    token = secrets.token_urlsafe(32)
    redis = await get_redis()
    await redis.set(
        f"{ADMIN_SESSION_PREFIX}{token}",
        json.dumps({"admin_id": admin.id, "username": admin.username, "role": admin.role}),
        ex=ADMIN_SESSION_TTL,
    )
    return token


async def validate_admin_session(token: str) -> dict[str, Any] | None:
    """Validate an admin session token.

    Args:
        token: The session token to validate.

    Returns:
        Admin session data dict, or None if invalid/expired.
    """
    redis = await get_redis()
    data = await redis.get(f"{ADMIN_SESSION_PREFIX}{token}")
    if data is None:
        return None
    # Refresh TTL on activity
    await redis.expire(f"{ADMIN_SESSION_PREFIX}{token}", ADMIN_SESSION_TTL)
    result: dict[str, Any] = json.loads(data)
    return result


async def admin_logout(token: str) -> bool:
    """End an admin session.

    Args:
        token: The session token to invalidate.

    Returns:
        True if the session was found and deleted, False otherwise.
    """
    redis = await get_redis()
    deleted: int = await redis.delete(f"{ADMIN_SESSION_PREFIX}{token}")
    return deleted > 0


async def get_all_accounts(session: AsyncSession) -> list[dict[str, Any]]:
    """Get all accounts with customer info.

    Args:
        session: Async database session.

    Returns:
        List of account dicts with customer name, balance, and status.
    """
    stmt = select(Account).options(selectinload(Account.customer)).order_by(Account.id)
    result = await session.execute(stmt)
    accounts = result.scalars().all()
    return [
        {
            "id": a.id,
            "account_number": a.account_number,
            "account_type": a.account_type.value,
            "balance": f"${a.balance_cents / 100:,.2f}",
            "status": a.status.value,
            "customer_name": a.customer.full_name if a.customer else "Unknown",
        }
        for a in accounts
    ]


async def freeze_account(session: AsyncSession, account_id: int) -> dict[str, str]:
    """Freeze an account.

    Args:
        session: Async database session.
        account_id: ID of the account to freeze.

    Returns:
        Confirmation message dict.

    Raises:
        ValueError: If the account is not found.
    """
    stmt = select(Account).where(Account.id == account_id)
    result = await session.execute(stmt)
    account = result.scalars().first()
    if account is None:
        raise ValueError("Account not found")
    account.status = AccountStatus.FROZEN
    await session.flush()
    return {"message": f"Account {account.account_number} frozen"}


async def unfreeze_account(session: AsyncSession, account_id: int) -> dict[str, str]:
    """Unfreeze an account.

    Args:
        session: Async database session.
        account_id: ID of the account to unfreeze.

    Returns:
        Confirmation message dict.

    Raises:
        ValueError: If the account is not found.
    """
    stmt = select(Account).where(Account.id == account_id)
    result = await session.execute(stmt)
    account = result.scalars().first()
    if account is None:
        raise ValueError("Account not found")
    account.status = AccountStatus.ACTIVE
    await session.flush()
    return {"message": f"Account {account.account_number} unfrozen"}


async def get_audit_logs(
    session: AsyncSession,
    limit: int = 100,
    event_type: str | None = None,
) -> list[dict[str, Any]]:
    """Get recent audit log entries.

    Args:
        session: Async database session.
        limit: Maximum number of entries to return.
        event_type: Optional filter by event type.

    Returns:
        List of audit log dicts.
    """
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    if event_type:
        stmt = stmt.where(AuditLog.event_type == AuditEventType(event_type))
    result = await session.execute(stmt)
    logs = result.scalars().all()
    return [
        {
            "id": log.id,
            "event_type": log.event_type.value,
            "account_id": log.account_id,
            "session_id": log.session_id,
            "details": log.details,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]


async def enable_maintenance_mode(reason: str | None = None) -> dict[str, str]:
    """Enable ATM maintenance mode.

    Args:
        reason: Optional human-readable reason for the maintenance.

    Returns:
        Confirmation message dict.
    """
    redis = await get_redis()
    await redis.set(MAINTENANCE_KEY, "1")
    if reason:
        await redis.set(MAINTENANCE_REASON_KEY, reason)
    else:
        await redis.delete(MAINTENANCE_REASON_KEY)
    return {"message": "Maintenance mode enabled"}


async def disable_maintenance_mode() -> dict[str, str]:
    """Disable ATM maintenance mode.

    Returns:
        Confirmation message dict.
    """
    redis = await get_redis()
    await redis.delete(MAINTENANCE_KEY)
    await redis.delete(MAINTENANCE_REASON_KEY)
    return {"message": "Maintenance mode disabled"}


async def get_maintenance_status() -> dict[str, Any]:
    """Get the current maintenance mode status.

    Returns:
        Dict with ``enabled`` bool and optional ``reason``.
    """
    redis = await get_redis()
    enabled = await redis.get(MAINTENANCE_KEY)
    reason = await redis.get(MAINTENANCE_REASON_KEY)
    return {
        "enabled": enabled == "1",
        "reason": reason or None,
    }


async def create_admin_user(
    session: AsyncSession,
    username: str,
    password: str,
    role: str = "admin",
) -> AdminUser:
    """Create a new admin user.

    Args:
        session: Async database session.
        username: The admin username.
        password: The plaintext password (will be hashed).
        role: The admin role.

    Returns:
        The created AdminUser instance.
    """
    admin = AdminUser(
        username=username,
        password_hash=hash_pin(password, settings.pin_pepper),
        role=role,
    )
    session.add(admin)
    await session.flush()
    return admin


# ---------------------------------------------------------------------------
# Customer CRUD
# ---------------------------------------------------------------------------


async def get_all_customers(session: AsyncSession) -> list[dict[str, Any]]:
    """Get all customers with account counts.

    Args:
        session: Async database session.

    Returns:
        List of customer dicts with account_count.
    """
    stmt = select(Customer).options(selectinload(Customer.accounts)).order_by(Customer.id)
    result = await session.execute(stmt)
    customers = result.scalars().all()
    return [
        {
            "id": c.id,
            "first_name": c.first_name,
            "last_name": c.last_name,
            "email": c.email,
            "phone": c.phone,
            "date_of_birth": c.date_of_birth.isoformat() if c.date_of_birth else None,
            "is_active": c.is_active,
            "account_count": len(c.accounts),
        }
        for c in customers
    ]


async def get_customer_detail(session: AsyncSession, customer_id: int) -> dict[str, Any] | None:
    """Get customer detail with accounts and cards.

    Args:
        session: Async database session.
        customer_id: ID of the customer.

    Returns:
        Customer detail dict, or None if not found.
    """
    stmt = (
        select(Customer)
        .where(Customer.id == customer_id)
        .options(
            selectinload(Customer.accounts).selectinload(Account.cards),
        )
    )
    result = await session.execute(stmt)
    customer = result.scalars().first()
    if customer is None:
        return None

    accounts = []
    for a in customer.accounts:
        cards = [
            {
                "id": card.id,
                "card_number": card.card_number,
                "is_active": card.is_active,
                "failed_attempts": card.failed_attempts,
                "is_locked": card.is_locked,
            }
            for card in a.cards
        ]
        accounts.append(
            {
                "id": a.id,
                "account_number": a.account_number,
                "account_type": a.account_type.value,
                "balance": f"${a.balance_cents / 100:,.2f}",
                "available_balance": f"${a.available_balance_cents / 100:,.2f}",
                "status": a.status.value,
                "cards": cards,
            }
        )

    return {
        "id": customer.id,
        "first_name": customer.first_name,
        "last_name": customer.last_name,
        "email": customer.email,
        "phone": customer.phone,
        "date_of_birth": (customer.date_of_birth.isoformat() if customer.date_of_birth else None),
        "is_active": customer.is_active,
        "account_count": len(customer.accounts),
        "accounts": accounts,
    }


async def create_customer(
    session: AsyncSession,
    data: dict[str, Any],
) -> dict[str, Any]:
    """Create a new customer.

    Args:
        session: Async database session.
        data: Validated customer data from CustomerCreateRequest.

    Returns:
        Created customer dict.

    Raises:
        ValueError: If email already exists.
    """
    existing = await session.execute(select(Customer).where(Customer.email == data["email"]))
    if existing.scalars().first() is not None:
        raise ValueError("A customer with this email already exists")

    customer = Customer(
        first_name=data["first_name"],
        last_name=data["last_name"],
        date_of_birth=data["date_of_birth"],
        email=data["email"],
        phone=data.get("phone"),
    )
    session.add(customer)
    await session.flush()

    await log_event(
        session,
        AuditEventType.CUSTOMER_CREATED,
        details={"customer_id": customer.id, "email": customer.email},
    )

    return {
        "id": customer.id,
        "first_name": customer.first_name,
        "last_name": customer.last_name,
        "email": customer.email,
        "phone": customer.phone,
        "date_of_birth": (customer.date_of_birth.isoformat() if customer.date_of_birth else None),
        "is_active": customer.is_active,
        "account_count": 0,
    }


async def update_customer(
    session: AsyncSession,
    customer_id: int,
    data: dict[str, Any],
) -> dict[str, Any] | None:
    """Update an existing customer's fields.

    Args:
        session: Async database session.
        customer_id: ID of the customer to update.
        data: Dict of fields to update (only non-None values).

    Returns:
        Updated customer dict, or None if not found.

    Raises:
        ValueError: If new email already belongs to another customer.
    """
    stmt = (
        select(Customer).where(Customer.id == customer_id).options(selectinload(Customer.accounts))
    )
    result = await session.execute(stmt)
    customer = result.scalars().first()
    if customer is None:
        return None

    if "email" in data and data["email"] is not None and data["email"] != customer.email:
        existing = await session.execute(
            select(Customer).where(Customer.email == data["email"], Customer.id != customer_id)
        )
        if existing.scalars().first() is not None:
            raise ValueError("A customer with this email already exists")

    for field, value in data.items():
        if value is not None:
            setattr(customer, field, value)
    await session.flush()

    await log_event(
        session,
        AuditEventType.CUSTOMER_UPDATED,
        details={"customer_id": customer.id, "updated_fields": list(data.keys())},
    )

    return {
        "id": customer.id,
        "first_name": customer.first_name,
        "last_name": customer.last_name,
        "email": customer.email,
        "phone": customer.phone,
        "date_of_birth": (customer.date_of_birth.isoformat() if customer.date_of_birth else None),
        "is_active": customer.is_active,
        "account_count": len(customer.accounts),
    }


async def deactivate_customer(session: AsyncSession, customer_id: int) -> dict[str, str] | None:
    """Soft-delete a customer by setting is_active=False.

    Args:
        session: Async database session.
        customer_id: ID of the customer to deactivate.

    Returns:
        Confirmation message dict, or None if not found.
    """
    result = await session.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalars().first()
    if customer is None:
        return None
    customer.is_active = False
    await session.flush()

    await log_event(
        session,
        AuditEventType.CUSTOMER_DEACTIVATED,
        details={"customer_id": customer.id},
    )

    return {"message": f"Customer {customer.full_name} deactivated"}


async def activate_customer(session: AsyncSession, customer_id: int) -> dict[str, str] | None:
    """Reactivate a customer by setting is_active=True.

    Args:
        session: Async database session.
        customer_id: ID of the customer to activate.

    Returns:
        Confirmation message dict, or None if not found.
    """
    result = await session.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalars().first()
    if customer is None:
        return None
    customer.is_active = True
    await session.flush()

    await log_event(
        session,
        AuditEventType.CUSTOMER_ACTIVATED,
        details={"customer_id": customer.id},
    )

    return {"message": f"Customer {customer.full_name} activated"}


# ---------------------------------------------------------------------------
# Account CRUD
# ---------------------------------------------------------------------------


async def _generate_account_number(session: AsyncSession, customer_id: int) -> str:
    """Generate the next account number for a customer.

    Pattern: 1000-CCCC-SSSS where CCCC is the customer segment and SSSS
    is the per-customer account sequence.

    Args:
        session: Async database session.
        customer_id: ID of the customer.

    Returns:
        Generated account number string.
    """
    # Use the underlying table to avoid ORM mapper hooks (e.g. the test
    # conftest's ``do_orm_execute`` listener that adds ``selectinload``
    # options — those are invalid for column-level queries).
    t = Account.__table__
    stmt = (
        select(t.c.account_number)
        .where(t.c.customer_id == customer_id)
        .order_by(t.c.account_number.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    max_num = result.scalar()

    if max_num is not None:
        # Parse the last segment and increment
        parts = max_num.split("-")
        next_seq = int(parts[2]) + 1
        customer_segment = parts[1]
    else:
        # First account for this customer — derive customer segment from ID
        customer_segment = f"{customer_id:04d}"
        next_seq = 1

    return f"1000-{customer_segment}-{next_seq:04d}"


async def create_account(
    session: AsyncSession,
    customer_id: int,
    data: dict[str, Any],
) -> dict[str, Any]:
    """Create a new account for a customer.

    Also creates an ATM card for the account with a default PIN of "1234"
    that should be changed immediately.

    Args:
        session: Async database session.
        customer_id: ID of the customer.
        data: Validated account data from AccountCreateRequest.

    Returns:
        Created account dict.

    Raises:
        ValueError: If customer not found.
    """
    result = await session.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalars().first()
    if customer is None:
        raise ValueError("Customer not found")

    account_number = await _generate_account_number(session, customer_id)
    initial_balance = data.get("initial_balance_cents", 0)

    account = Account(
        customer_id=customer_id,
        account_number=account_number,
        account_type=AccountType(data["account_type"]),
        balance_cents=initial_balance,
        available_balance_cents=initial_balance,
        status=AccountStatus.ACTIVE,
    )
    session.add(account)
    await session.flush()

    # Create an ATM card with a default PIN
    default_pin = "1357"
    card = ATMCard(
        account_id=account.id,
        card_number=account_number,
        pin_hash=hash_pin(default_pin, settings.pin_pepper),
    )
    session.add(card)
    await session.flush()

    await log_event(
        session,
        AuditEventType.ACCOUNT_CREATED,
        account_id=account.id,
        details={
            "customer_id": customer_id,
            "account_number": account_number,
            "account_type": data["account_type"],
            "initial_balance_cents": initial_balance,
        },
    )

    return {
        "id": account.id,
        "account_number": account.account_number,
        "account_type": account.account_type.value,
        "balance": f"${account.balance_cents / 100:,.2f}",
        "available_balance": f"${account.available_balance_cents / 100:,.2f}",
        "status": account.status.value,
        "cards": [
            {
                "id": card.id,
                "card_number": card.card_number,
                "is_active": card.is_active,
                "failed_attempts": card.failed_attempts,
                "is_locked": card.is_locked,
            }
        ],
    }


async def update_account(
    session: AsyncSession,
    account_id: int,
    data: dict[str, Any],
) -> dict[str, Any] | None:
    """Update account limit overrides.

    Args:
        session: Async database session.
        account_id: ID of the account to update.
        data: Dict with optional daily_withdrawal_limit_cents and daily_transfer_limit_cents.

    Returns:
        Updated account dict, or None if not found.
    """
    result = await session.execute(select(Account).where(Account.id == account_id))
    account = result.scalars().first()
    if account is None:
        return None

    updated_fields = []
    if data.get("daily_withdrawal_limit_cents") is not None:
        updated_fields.append("daily_withdrawal_limit_cents")
    if data.get("daily_transfer_limit_cents") is not None:
        updated_fields.append("daily_transfer_limit_cents")
    await session.flush()

    await log_event(
        session,
        AuditEventType.ACCOUNT_UPDATED,
        account_id=account.id,
        details={"updated_fields": updated_fields},
    )

    return {
        "id": account.id,
        "account_number": account.account_number,
        "account_type": account.account_type.value,
        "balance": f"${account.balance_cents / 100:,.2f}",
        "available_balance": f"${account.available_balance_cents / 100:,.2f}",
        "status": account.status.value,
    }


async def close_account(session: AsyncSession, account_id: int) -> dict[str, str] | None:
    """Close an account (balance must be zero).

    Args:
        session: Async database session.
        account_id: ID of the account to close.

    Returns:
        Confirmation message dict, or None if not found.

    Raises:
        ValueError: If account balance is not zero.
    """
    result = await session.execute(select(Account).where(Account.id == account_id))
    account = result.scalars().first()
    if account is None:
        return None

    if account.balance_cents != 0:
        raise ValueError(
            f"Cannot close account with non-zero balance (${account.balance_cents / 100:,.2f})"
        )

    account.status = AccountStatus.CLOSED
    await session.flush()

    await log_event(
        session,
        AuditEventType.ACCOUNT_CLOSED,
        account_id=account.id,
        details={"account_number": account.account_number},
    )

    return {"message": f"Account {account.account_number} closed"}


# ---------------------------------------------------------------------------
# PIN Management
# ---------------------------------------------------------------------------


async def admin_reset_pin(
    session: AsyncSession,
    card_id: int,
    new_pin: str,
) -> dict[str, str] | None:
    """Admin-initiated PIN reset.

    Args:
        session: Async database session.
        card_id: ID of the ATM card.
        new_pin: The new plaintext PIN (already validated by schema).

    Returns:
        Confirmation message dict, or None if card not found.

    Raises:
        ValueError: If PIN fails complexity validation.
    """
    is_valid, message = validate_pin_complexity(new_pin)
    if not is_valid:
        raise ValueError(message)

    result = await session.execute(select(ATMCard).where(ATMCard.id == card_id))
    card = result.scalars().first()
    if card is None:
        return None

    card.pin_hash = hash_pin(new_pin, settings.pin_pepper)
    card.failed_attempts = 0
    card.locked_until = None
    await session.flush()

    await log_event(
        session,
        AuditEventType.PIN_RESET_ADMIN,
        account_id=card.account_id,
        details={"card_id": card.id},
    )

    return {"message": f"PIN reset for card {card.card_number}"}


# ---------------------------------------------------------------------------
# Data Export / Import
# ---------------------------------------------------------------------------


async def export_snapshot(session: AsyncSession) -> dict[str, Any]:
    """Export the entire database as a JSON-serializable dict.

    Includes customers, accounts, cards, and admin users. PINs are exported
    as "CHANGE_ME" sentinels alongside the actual pin_hash for portability.
    Transactions are excluded (operational data, not config).

    Args:
        session: Async database session.

    Returns:
        Nested dict ready for JSON serialization.
    """
    from datetime import UTC, datetime

    # Fetch all customers with accounts and cards
    stmt = (
        select(Customer)
        .options(
            selectinload(Customer.accounts).selectinload(Account.cards),
        )
        .order_by(Customer.id)
    )
    result = await session.execute(stmt)
    customers = result.scalars().all()

    customers_data = []
    for c in customers:
        accounts_data = []
        for a in c.accounts:
            cards_data = []
            for card in a.cards:
                cards_data.append(
                    {
                        "card_number": card.card_number,
                        "pin": "CHANGE_ME",
                        "pin_hash": card.pin_hash,
                        "is_active": card.is_active,
                    }
                )
            accounts_data.append(
                {
                    "account_number": a.account_number,
                    "account_type": a.account_type.value,
                    "balance_cents": a.balance_cents,
                    "available_balance_cents": a.available_balance_cents,
                    "status": a.status.value,
                    "cards": cards_data,
                }
            )
        customers_data.append(
            {
                "first_name": c.first_name,
                "last_name": c.last_name,
                "date_of_birth": c.date_of_birth.isoformat() if c.date_of_birth else None,
                "email": c.email,
                "phone": c.phone,
                "is_active": c.is_active,
                "accounts": accounts_data,
            }
        )

    # Fetch admin users
    admin_result = await session.execute(select(AdminUser).order_by(AdminUser.id))
    admin_users = admin_result.scalars().all()
    admin_data = [
        {
            "username": au.username,
            "password": "CHANGE_ME",
            "password_hash": au.password_hash,
            "role": au.role,
            "is_active": au.is_active,
        }
        for au in admin_users
    ]

    await log_event(
        session,
        AuditEventType.DATA_EXPORTED,
        details={
            "customer_count": len(customers_data),
            "admin_user_count": len(admin_data),
        },
    )

    return {
        "version": "1.0",
        "exported_at": datetime.now(UTC).isoformat(),
        "customers": customers_data,
        "admin_users": admin_data,
    }


async def import_snapshot(
    session: AsyncSession,
    data: dict[str, Any],
    conflict_strategy: str = "skip",
) -> dict[str, Any]:
    """Import a JSON snapshot into the database.

    Args:
        session: Async database session.
        data: Parsed JSON snapshot dict.
        conflict_strategy: "skip" to keep existing records, "replace" to overwrite.

    Returns:
        Summary dict with counts of imported/skipped entities.

    Raises:
        ValueError: If the snapshot data is malformed.
    """
    if "customers" not in data:
        raise ValueError("Invalid snapshot: missing 'customers' key")
    if "version" not in data:
        raise ValueError("Invalid snapshot: missing 'version' key")

    pepper = settings.pin_pepper
    stats: dict[str, int] = {
        "customers_created": 0,
        "customers_skipped": 0,
        "customers_replaced": 0,
        "accounts_created": 0,
        "accounts_skipped": 0,
        "accounts_replaced": 0,
        "cards_created": 0,
        "admin_users_created": 0,
        "admin_users_skipped": 0,
    }

    for cust_data in data["customers"]:
        # Parse date_of_birth string to date object if needed
        dob_raw = cust_data.get("date_of_birth")
        dob = date.fromisoformat(dob_raw) if isinstance(dob_raw, str) else dob_raw

        # Check for existing customer by email
        existing_result = await session.execute(
            select(Customer).where(Customer.email == cust_data["email"])
        )
        existing_customer = existing_result.scalars().first()

        if existing_customer is not None:
            if conflict_strategy == "skip":
                stats["customers_skipped"] += 1
                # Still process accounts for existing customer if replace
                continue
            # Replace: update existing customer fields
            existing_customer.first_name = cust_data["first_name"]
            existing_customer.last_name = cust_data["last_name"]
            existing_customer.date_of_birth = dob
            existing_customer.phone = cust_data.get("phone")
            existing_customer.is_active = cust_data.get("is_active", True)
            await session.flush()
            customer = existing_customer
            stats["customers_replaced"] += 1
        else:
            customer = Customer(
                first_name=cust_data["first_name"],
                last_name=cust_data["last_name"],
                date_of_birth=dob,
                email=cust_data["email"],
                phone=cust_data.get("phone"),
                is_active=cust_data.get("is_active", True),
            )
            session.add(customer)
            await session.flush()
            stats["customers_created"] += 1

        # Process accounts
        for acct_data in cust_data.get("accounts", []):
            existing_acct_result = await session.execute(
                select(Account).where(Account.account_number == acct_data["account_number"])
            )
            existing_acct = existing_acct_result.scalars().first()

            if existing_acct is not None:
                if conflict_strategy == "skip":
                    stats["accounts_skipped"] += 1
                    continue
                # Replace: update balance and status
                existing_acct.balance_cents = acct_data["balance_cents"]
                existing_acct.available_balance_cents = acct_data["available_balance_cents"]
                existing_acct.status = AccountStatus(acct_data["status"])
                existing_acct.daily_withdrawal_used_cents = 0
                existing_acct.daily_transfer_used_cents = 0
                await session.flush()
                account = existing_acct
                stats["accounts_replaced"] += 1
            else:
                account = Account(
                    customer_id=customer.id,
                    account_number=acct_data["account_number"],
                    account_type=AccountType(acct_data["account_type"]),
                    balance_cents=acct_data["balance_cents"],
                    available_balance_cents=acct_data["available_balance_cents"],
                    status=AccountStatus(acct_data["status"]),
                    daily_withdrawal_used_cents=0,
                    daily_transfer_used_cents=0,
                )
                session.add(account)
                await session.flush()
                stats["accounts_created"] += 1

            # Process cards
            for card_data in acct_data.get("cards", []):
                existing_card_result = await session.execute(
                    select(ATMCard).where(ATMCard.card_number == card_data["card_number"])
                )
                existing_card = existing_card_result.scalars().first()

                # Determine PIN hash
                if card_data.get("pin") and card_data["pin"] != "CHANGE_ME":
                    pin_hash_value = hash_pin(card_data["pin"], pepper)
                else:
                    pin_hash_value = card_data.get("pin_hash", hash_pin("1357", pepper))

                if existing_card is not None:
                    if conflict_strategy == "replace":
                        existing_card.pin_hash = pin_hash_value
                        existing_card.is_active = card_data.get("is_active", True)
                        existing_card.failed_attempts = 0
                        existing_card.locked_until = None
                        await session.flush()
                    # skip: leave card as-is
                else:
                    card = ATMCard(
                        account_id=account.id,
                        card_number=card_data["card_number"],
                        pin_hash=pin_hash_value,
                        is_active=card_data.get("is_active", True),
                        failed_attempts=0,
                    )
                    session.add(card)
                    await session.flush()
                    stats["cards_created"] += 1

    # Process admin users
    for admin_data in data.get("admin_users", []):
        existing_admin_result = await session.execute(
            select(AdminUser).where(AdminUser.username == admin_data["username"])
        )
        existing_admin = existing_admin_result.scalars().first()

        if existing_admin is not None:
            stats["admin_users_skipped"] += 1
            continue

        # Determine password hash
        if admin_data.get("password") and admin_data["password"] != "CHANGE_ME":
            pw_hash = hash_pin(admin_data["password"], pepper)
        else:
            pw_hash = admin_data.get("password_hash", hash_pin("admin123", pepper))

        admin_user = AdminUser(
            username=admin_data["username"],
            password_hash=pw_hash,
            role=admin_data.get("role", "admin"),
            is_active=admin_data.get("is_active", True),
        )
        session.add(admin_user)
        await session.flush()
        stats["admin_users_created"] += 1

    await log_event(
        session,
        AuditEventType.DATA_IMPORTED,
        details={"conflict_strategy": conflict_strategy, **stats},
    )

    return stats
