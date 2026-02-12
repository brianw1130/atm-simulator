"""Initial schema.

Revision ID: 0001
Revises:
Create Date: 2026-02-11

Creates all core tables:
    - customers
    - accounts
    - transactions
    - atm_cards
    - audit_logs
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create all tables for the ATM simulator."""
    # -- customers --
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    # -- accounts --
    account_type_enum = sa.Enum("CHECKING", "SAVINGS", name="accounttype")
    account_status_enum = sa.Enum("ACTIVE", "FROZEN", "CLOSED", name="accountstatus")

    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("account_number", sa.String(20), nullable=False),
        sa.Column("account_type", account_type_enum, nullable=False),
        sa.Column("balance_cents", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "available_balance_cents", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column(
            "daily_withdrawal_used_cents",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "daily_transfer_used_cents",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("status", account_status_enum, nullable=False, server_default=sa.text("'ACTIVE'")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.UniqueConstraint("account_number"),
    )
    op.create_index("ix_accounts_customer_id", "accounts", ["customer_id"])

    # -- transactions --
    transaction_type_enum = sa.Enum(
        "WITHDRAWAL",
        "DEPOSIT_CASH",
        "DEPOSIT_CHECK",
        "TRANSFER_IN",
        "TRANSFER_OUT",
        "FEE",
        "INTEREST",
        name="transactiontype",
    )

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("transaction_type", transaction_type_enum, nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("balance_after_cents", sa.Integer(), nullable=False),
        sa.Column("reference_number", sa.String(36), nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("related_account_id", sa.Integer(), nullable=True),
        sa.Column("check_number", sa.String(20), nullable=True),
        sa.Column("hold_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"]),
        sa.ForeignKeyConstraint(["related_account_id"], ["accounts.id"]),
        sa.UniqueConstraint("reference_number"),
    )
    op.create_index("ix_transactions_account_id", "transactions", ["account_id"])
    op.create_index("ix_transactions_created_at", "transactions", ["created_at"])

    # -- atm_cards --
    op.create_table(
        "atm_cards",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("card_number", sa.String(20), nullable=False),
        sa.Column("pin_hash", sa.String(255), nullable=False),
        sa.Column("failed_attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"]),
        sa.UniqueConstraint("card_number"),
    )

    # -- audit_logs --
    audit_event_type_enum = sa.Enum(
        "LOGIN_SUCCESS",
        "LOGIN_FAILED",
        "ACCOUNT_LOCKED",
        "SESSION_EXPIRED",
        "LOGOUT",
        "WITHDRAWAL",
        "WITHDRAWAL_DECLINED",
        "DEPOSIT",
        "TRANSFER",
        "TRANSFER_DECLINED",
        "BALANCE_INQUIRY",
        "STATEMENT_GENERATED",
        "PIN_CHANGED",
        "PIN_CHANGE_FAILED",
        "ACCOUNT_FROZEN",
        "ACCOUNT_UNFROZEN",
        "VALIDATION_FAILURE",
        name="auditeventtype",
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("event_type", audit_event_type_enum, nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("session_id", sa.String(36), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"]),
    )
    op.create_index("ix_audit_logs_event_type", "audit_logs", ["event_type"])
    op.create_index("ix_audit_logs_account_id", "audit_logs", ["account_id"])
    op.create_index("ix_audit_logs_session_id", "audit_logs", ["session_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    """Drop all tables in reverse dependency order."""
    op.drop_table("audit_logs")
    op.drop_table("atm_cards")
    op.drop_table("transactions")
    op.drop_table("accounts")
    op.drop_table("customers")

    # Drop enum types
    sa.Enum(name="auditeventtype").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="transactiontype").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="accountstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="accounttype").drop(op.get_bind(), checkfirst=True)
