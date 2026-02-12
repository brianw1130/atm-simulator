"""Account model representing a bank account (checking or savings)."""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.atm.models import Base


class AccountType(str, enum.Enum):
    """Types of bank accounts."""

    CHECKING = "CHECKING"
    SAVINGS = "SAVINGS"


class AccountStatus(str, enum.Enum):
    """Account status values."""

    ACTIVE = "ACTIVE"
    FROZEN = "FROZEN"
    CLOSED = "CLOSED"


class Account(Base):
    """A bank account belonging to a customer.

    Balances are stored in cents (integer) to avoid floating-point precision issues.

    Attributes:
        id: Unique account identifier.
        customer_id: Foreign key to the owning customer.
        account_number: Human-readable account number (e.g., 1000-0001-0001).
        account_type: CHECKING or SAVINGS.
        balance_cents: Total balance in cents.
        available_balance_cents: Available balance in cents (may differ from total due to holds).
        daily_withdrawal_used_cents: Amount withdrawn today in cents (resets daily).
        daily_transfer_used_cents: Amount transferred today in cents (resets daily).
        status: ACTIVE, FROZEN, or CLOSED.
        created_at: Timestamp of record creation.
        updated_at: Timestamp of last update.
    """

    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"), nullable=False, index=True
    )
    account_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    account_type: Mapped[AccountType] = mapped_column(
        Enum(AccountType), nullable=False
    )
    balance_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    available_balance_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    daily_withdrawal_used_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    daily_transfer_used_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus), default=AccountStatus.ACTIVE, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    customer: Mapped["Customer"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="accounts", lazy="selectin"
    )
    transactions: Mapped[list["Transaction"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="account",
        lazy="selectin",
        order_by="Transaction.created_at.desc()",
        foreign_keys="[Transaction.account_id]",
    )
    cards: Mapped[list["ATMCard"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="account", lazy="selectin"
    )

    @property
    def balance_dollars(self) -> str:
        """Return balance formatted as dollars (e.g., '$1,234.56')."""
        dollars = self.balance_cents / 100
        return f"${dollars:,.2f}"

    @property
    def available_balance_dollars(self) -> str:
        """Return available balance formatted as dollars."""
        dollars = self.available_balance_cents / 100
        return f"${dollars:,.2f}"

    @property
    def masked_account_number(self) -> str:
        """Return account number with all but last 4 characters masked."""
        if len(self.account_number) <= 4:
            return self.account_number
        return "X" * (len(self.account_number) - 4) + self.account_number[-4:]

    @property
    def is_active(self) -> bool:
        """Check if account is in active status."""
        return self.status == AccountStatus.ACTIVE
