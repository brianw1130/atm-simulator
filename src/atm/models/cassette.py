"""Cash cassette model for ATM bill inventory tracking."""

from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from src.atm.models import Base


class CashCassette(Base):
    """Represents a physical cash cassette in the ATM.

    Each cassette holds bills of a single denomination.

    Attributes:
        id: Primary key.
        denomination_cents: Bill value in cents (e.g., 2000 = $20).
        bill_count: Current number of bills in the cassette.
        max_capacity: Maximum number of bills the cassette can hold.
        last_refilled_at: When the cassette was last refilled.
        created_at: When the cassette record was created.
    """

    __tablename__ = "cash_cassettes"

    id: Mapped[int] = mapped_column(primary_key=True)
    denomination_cents: Mapped[int] = mapped_column(nullable=False)
    bill_count: Mapped[int] = mapped_column(default=0)
    max_capacity: Mapped[int] = mapped_column(default=2000)
    last_refilled_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
