"""Widen audit_logs.session_id from VARCHAR(36) to VARCHAR(64).

Revision ID: 0003
Revises: 0002
Create Date: 2026-02-12

token_urlsafe(32) produces 44-character strings which exceed VARCHAR(36).
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "audit_logs",
        "session_id",
        type_=sa.String(64),
        existing_type=sa.String(36),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "audit_logs",
        "session_id",
        type_=sa.String(36),
        existing_type=sa.String(64),
        existing_nullable=True,
    )
