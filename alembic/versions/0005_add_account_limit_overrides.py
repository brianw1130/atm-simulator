"""Add per-account limit override columns.

Revision ID: 0005
Revises: 0004
Create Date: 2026-02-14

Adds nullable daily_withdrawal_limit_cents and daily_transfer_limit_cents
columns to the accounts table for per-account limit overrides. When NULL,
the global config limit applies.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "accounts", sa.Column("daily_withdrawal_limit_cents", sa.Integer(), nullable=True)
    )
    op.add_column("accounts", sa.Column("daily_transfer_limit_cents", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("accounts", "daily_transfer_limit_cents")
    op.drop_column("accounts", "daily_withdrawal_limit_cents")
