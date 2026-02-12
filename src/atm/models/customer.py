"""Customer model representing a bank customer."""

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.atm.models import Base


class Customer(Base):
    """A bank customer who may hold one or more accounts.

    Attributes:
        id: Unique customer identifier.
        first_name: Customer's first name.
        last_name: Customer's last name.
        date_of_birth: Customer's date of birth.
        email: Customer's email address (unique).
        phone: Customer's phone number.
        is_active: Whether the customer account is active.
        created_at: Timestamp of record creation.
        updated_at: Timestamp of last update.
    """

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    accounts: Mapped[list["Account"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="customer", lazy="selectin"
    )

    @property
    def full_name(self) -> str:
        """Return the customer's full name."""
        return f"{self.first_name} {self.last_name}"
