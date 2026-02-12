"""ATM Card model representing a physical ATM card linked to an account."""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.atm.models import Base


def _utcnow_naive() -> datetime:
    """Return current UTC time as a naive datetime for DB compatibility."""
    return datetime.now(UTC).replace(tzinfo=None)


class ATMCard(Base):
    """An ATM card linked to a bank account.

    PINs are stored as bcrypt hashes — never in plaintext.

    Attributes:
        id: Unique card identifier.
        account_id: Foreign key to the linked account.
        card_number: Card number used for authentication.
        pin_hash: Bcrypt hash of the card's PIN.
        failed_attempts: Number of consecutive failed PIN attempts.
        locked_until: If locked, the datetime when lockout expires.
        is_active: Whether the card is active.
        created_at: Timestamp of record creation.
        updated_at: Timestamp of last update.
    """

    __tablename__ = "atm_cards"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    card_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    pin_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    account: Mapped["Account"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="cards"
    )

    @property
    def is_locked(self) -> bool:
        """Check if the card is currently locked due to failed PIN attempts."""
        if self.locked_until is None:
            return False
        # Compare as naive UTC to avoid issues with SQLite stripping tzinfo
        locked = self.locked_until.replace(tzinfo=None)
        return _utcnow_naive() < locked
