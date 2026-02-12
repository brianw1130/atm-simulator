"""SQLAlchemy ORM models for the ATM simulator."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


# Import all models so Alembic can detect them
from src.atm.models.account import Account  # noqa: E402, F401
from src.atm.models.admin import AdminUser  # noqa: E402, F401
from src.atm.models.audit import AuditLog  # noqa: E402, F401
from src.atm.models.card import ATMCard  # noqa: E402, F401
from src.atm.models.cassette import CashCassette  # noqa: E402, F401
from src.atm.models.customer import Customer  # noqa: E402, F401
from src.atm.models.transaction import Transaction  # noqa: E402, F401
