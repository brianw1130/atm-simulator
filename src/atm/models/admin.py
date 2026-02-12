"""Admin user model for the admin panel."""

from datetime import datetime

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.atm.models import Base


class AdminUser(Base):
    """An administrator who can manage accounts and view audit logs.

    Attributes:
        id: Primary key.
        username: Unique login username.
        password_hash: bcrypt hash of the password.
        role: Admin role (for future RBAC).
        is_active: Whether the admin account is active.
        created_at: When the admin was created.
    """

    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="admin")
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
