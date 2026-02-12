"""Audit service for logging all security-relevant events.

Owner: Security Engineer + Backend Engineer
Coverage requirement: 100%

Responsibilities:
    - Log authentication events (success, failure, lockout)
    - Log transaction events (all types, including declined)
    - Log administrative actions
    - Provide audit trail queries for admin panel
"""

from sqlalchemy.ext.asyncio import AsyncSession

from src.atm.models.audit import AuditEventType, AuditLog


async def log_event(
    session: AsyncSession,
    event_type: AuditEventType,
    account_id: int | None = None,
    ip_address: str | None = None,
    session_id: str | None = None,
    details: dict[str, object] | None = None,
) -> AuditLog:
    """Create an audit log entry for a security-relevant event.

    Records the event in the audit_logs table and flushes immediately so
    the record is visible within the current transaction.

    Args:
        session: Async SQLAlchemy session for database operations.
        event_type: The category of event being logged.
        account_id: Associated account ID, if applicable.
        ip_address: Client IP address, if available.
        session_id: Session identifier for event correlation.
        details: Additional event-specific metadata stored as JSON.

    Returns:
        The created AuditLog record with its generated ID.
    """
    audit_entry = AuditLog(
        event_type=event_type,
        account_id=account_id,
        ip_address=ip_address,
        session_id=session_id,
        details=details,
    )
    session.add(audit_entry)
    await session.flush()
    return audit_entry
