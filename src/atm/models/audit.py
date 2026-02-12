"""Audit log model for tracking all security-relevant events."""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.atm.models import Base


class AuditEventType(str, enum.Enum):
    """Types of auditable events."""

    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    LOGOUT = "LOGOUT"
    WITHDRAWAL = "WITHDRAWAL"
    WITHDRAWAL_DECLINED = "WITHDRAWAL_DECLINED"
    DEPOSIT = "DEPOSIT"
    TRANSFER = "TRANSFER"
    TRANSFER_DECLINED = "TRANSFER_DECLINED"
    BALANCE_INQUIRY = "BALANCE_INQUIRY"
    STATEMENT_GENERATED = "STATEMENT_GENERATED"
    PIN_CHANGED = "PIN_CHANGED"
    PIN_CHANGE_FAILED = "PIN_CHANGE_FAILED"
    ACCOUNT_FROZEN = "ACCOUNT_FROZEN"
    ACCOUNT_UNFROZEN = "ACCOUNT_UNFROZEN"
    VALIDATION_FAILURE = "VALIDATION_FAILURE"


class AuditLog(Base):
    """An immutable audit log entry.

    Every authentication attempt, transaction, and administrative action
    is recorded for compliance and security monitoring.

    Attributes:
        id: Unique log entry identifier.
        event_type: Category of the audited event.
        account_id: Associated account (nullable for pre-auth events).
        ip_address: Client IP address.
        session_id: Session identifier for correlating related events.
        details: JSON blob with event-specific metadata.
        created_at: Timestamp of the event.
    """

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_type: Mapped[AuditEventType] = mapped_column(
        Enum(AuditEventType), nullable=False, index=True
    )
    account_id: Mapped[int | None] = mapped_column(
        ForeignKey("accounts.id"), nullable=True, index=True
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # type: ignore[assignment]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
