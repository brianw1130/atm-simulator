"""Phase 2 models — admin users and cash cassettes.

Revision ID: 0002
Revises: 0001
Create Date: 2026-02-12

Adds:
    - admin_users: Admin panel authentication
    - cash_cassettes: ATM bill inventory tracking
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add admin_users and cash_cassettes tables."""
    op.create_table(
        "admin_users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("password_hash", sa.String(128), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default=sa.text("'admin'")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )

    op.create_table(
        "cash_cassettes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("denomination_cents", sa.Integer(), nullable=False),
        sa.Column("bill_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("max_capacity", sa.Integer(), nullable=False, server_default=sa.text("2000")),
        sa.Column("last_refilled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Remove Phase 2 tables."""
    op.drop_table("cash_cassettes")
    op.drop_table("admin_users")
