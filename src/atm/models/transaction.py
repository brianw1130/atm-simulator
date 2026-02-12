"""Transaction model representing a financial transaction on an account."""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.atm.models import Base


class TransactionType(str, enum.Enum):
    """Types of transactions."""

    WITHDRAWAL = "WITHDRAWAL"
    DEPOSIT_CASH = "DEPOSIT_CASH"
    DEPOSIT_CHECK = "DEPOSIT_CHECK"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"
    FEE = "FEE"
    INTEREST = "INTEREST"


class Transaction(Base):
    """A financial transaction on an account.

    All monetary amounts are stored in cents (integer).

    Attributes:
        id: Unique transaction identifier.
        account_id: Foreign key to the account.
        transaction_type: Type of transaction.
        amount_cents: Transaction amount in cents (always positive).
        balance_after_cents: Account balance after this transaction in cents.
        reference_number: Unique reference for receipts.
        description: Human-readable description.
        related_account_id: For transfers, the other account involved.
        check_number: For check deposits, the check number.
        hold_until: For deposits with holds, when the hold expires.
        metadata_json: Additional transaction metadata.
        created_at: Timestamp of the transaction.
    """

    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id"), nullable=False, index=True
    )
    transaction_type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType), nullable=False
    )
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_number: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    related_account_id: Mapped[int | None] = mapped_column(
        ForeignKey("accounts.id"), nullable=True
    )
    check_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    hold_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # type: ignore[assignment]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    account: Mapped["Account"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="transactions", foreign_keys=[account_id]
    )

    @property
    def amount_dollars(self) -> str:
        """Return amount formatted as dollars."""
        dollars = self.amount_cents / 100
        return f"${dollars:,.2f}"

    @property
    def is_debit(self) -> bool:
        """Check if this transaction reduces the account balance."""
        return self.transaction_type in (
            TransactionType.WITHDRAWAL,
            TransactionType.TRANSFER_OUT,
            TransactionType.FEE,
        )

    @property
    def is_credit(self) -> bool:
        """Check if this transaction increases the account balance."""
        return self.transaction_type in (
            TransactionType.DEPOSIT_CASH,
            TransactionType.DEPOSIT_CHECK,
            TransactionType.TRANSFER_IN,
            TransactionType.INTEREST,
        )
