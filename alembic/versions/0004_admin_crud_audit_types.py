"""Add admin CRUD audit event types.

Revision ID: 0004
Revises: 0003
Create Date: 2026-02-14

Adds new AuditEventType enum values for admin CRUD operations:
CUSTOMER_CREATED, CUSTOMER_UPDATED, CUSTOMER_DEACTIVATED, CUSTOMER_ACTIVATED,
ACCOUNT_CREATED, ACCOUNT_UPDATED, ACCOUNT_CLOSED, PIN_RESET_ADMIN,
DATA_EXPORTED, DATA_IMPORTED.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NEW_VALUES = [
    "CUSTOMER_CREATED",
    "CUSTOMER_UPDATED",
    "CUSTOMER_DEACTIVATED",
    "CUSTOMER_ACTIVATED",
    "ACCOUNT_CREATED",
    "ACCOUNT_UPDATED",
    "ACCOUNT_CLOSED",
    "PIN_RESET_ADMIN",
    "DATA_EXPORTED",
    "DATA_IMPORTED",
]


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for value in NEW_VALUES:
            op.execute(f"ALTER TYPE auditeventtype ADD VALUE IF NOT EXISTS '{value}'")
    # SQLite stores enums as VARCHAR — no schema change needed.


def downgrade() -> None:
    # PostgreSQL does not support removing values from an enum type.
    # SQLite stores enums as VARCHAR — no schema change needed.
    pass
