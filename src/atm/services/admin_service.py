"""Admin service for account management and audit log access."""

import json
import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.atm.config import settings
from src.atm.models.account import Account, AccountStatus
from src.atm.models.admin import AdminUser
from src.atm.models.audit import AuditEventType, AuditLog
from src.atm.services.redis_client import get_redis
from src.atm.utils.security import hash_pin, verify_pin

ADMIN_SESSION_PREFIX = "admin_session:"
ADMIN_SESSION_TTL = 1800  # 30 minutes


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


async def validate_admin_session(token: str) -> dict | None:
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
    return json.loads(data)


async def admin_logout(token: str) -> bool:
    """End an admin session.

    Args:
        token: The session token to invalidate.

    Returns:
        True if the session was found and deleted, False otherwise.
    """
    redis = await get_redis()
    deleted = await redis.delete(f"{ADMIN_SESSION_PREFIX}{token}")
    return deleted > 0


async def get_all_accounts(session: AsyncSession) -> list[dict]:
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


async def freeze_account(session: AsyncSession, account_id: int) -> dict:
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


async def unfreeze_account(session: AsyncSession, account_id: int) -> dict:
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
) -> list[dict]:
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
