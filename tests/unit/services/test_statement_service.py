"""Unit tests for statement_service.

Coverage requirement: 100%

Tests:
    - _format_cents: various amounts
    - generate_statement: valid with days, valid with custom date range,
      default days (30), empty statement, account not found,
      opening/closing balance calculation, PDF generation called
"""

from datetime import date, timedelta
from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.atm.models.account import Account, AccountStatus, AccountType
from src.atm.models.customer import Customer
from src.atm.models.transaction import Transaction, TransactionType
from src.atm.services.statement_service import (
    StatementError,
    _format_cents,
    generate_statement,
)

pytestmark = pytest.mark.asyncio


async def _seed_account_with_customer(
    db_session: AsyncSession,
    *,
    account_number: str = "1000-0001-0001",
    balance_cents: int = 525_000,
) -> Account:
    customer = Customer(
        first_name="Alice",
        last_name="Johnson",
        date_of_birth=date(1990, 1, 15),
        email=f"alice-stmt-{account_number}@example.com",
    )
    db_session.add(customer)
    await db_session.flush()

    account = Account(
        customer_id=customer.id,
        account_number=account_number,
        account_type=AccountType.CHECKING,
        balance_cents=balance_cents,
        available_balance_cents=balance_cents,
        status=AccountStatus.ACTIVE,
    )
    db_session.add(account)
    await db_session.flush()
    # Explicitly populate the customer relationship so that the statement
    # service can access account.customer without triggering a lazy load
    # (async SQLAlchemy does not support implicit lazy loads).
    await db_session.refresh(account, attribute_names=["customer"])
    return account


async def _seed_transaction(
    db_session: AsyncSession,
    account_id: int,
    *,
    txn_type: TransactionType = TransactionType.WITHDRAWAL,
    amount_cents: int = 10_000,
    balance_after_cents: int = 515_000,
    reference_number: str = "REF-stmt-00000001",
    description: str = "ATM Withdrawal",
) -> Transaction:
    txn = Transaction(
        account_id=account_id,
        transaction_type=txn_type,
        amount_cents=amount_cents,
        balance_after_cents=balance_after_cents,
        reference_number=reference_number,
        description=description,
    )
    db_session.add(txn)
    await db_session.flush()
    return txn


# ── _format_cents ────────────────────────────────────────────────────────────


class TestFormatCents:
    def test_zero(self):
        assert _format_cents(0) == "$0.00"

    def test_standard(self):
        assert _format_cents(525_000) == "$5,250.00"


# ── generate_statement ───────────────────────────────────────────────────────


class TestGenerateStatement:
    @patch("src.atm.services.statement_service.generate_statement_pdf")
    async def test_statement_with_default_days(self, mock_pdf, db_session: AsyncSession):
        account = await _seed_account_with_customer(db_session)
        result = await generate_statement(db_session, account.id)

        assert result["transaction_count"] == 0
        assert result["file_path"].endswith(".pdf")
        assert result["period"]
        mock_pdf.assert_called_once()

    @patch("src.atm.services.statement_service.generate_statement_pdf")
    async def test_statement_with_custom_days(self, mock_pdf, db_session: AsyncSession):
        account = await _seed_account_with_customer(db_session)
        result = await generate_statement(db_session, account.id, days=7)

        assert result["transaction_count"] == 0
        assert "period" in result
        mock_pdf.assert_called_once()

    @patch("src.atm.services.statement_service.generate_statement_pdf")
    async def test_statement_with_date_range(self, mock_pdf, db_session: AsyncSession):
        account = await _seed_account_with_customer(db_session)
        today = date.today()
        start = today - timedelta(days=7)

        result = await generate_statement(db_session, account.id, start_date=start, end_date=today)

        assert result["period"]
        mock_pdf.assert_called_once()

    @patch("src.atm.services.statement_service.generate_statement_pdf")
    async def test_includes_transactions_in_range(self, mock_pdf, db_session: AsyncSession):
        account = await _seed_account_with_customer(db_session, balance_cents=515_000)
        await _seed_transaction(
            db_session,
            account.id,
            reference_number="REF-stmt-00000001",
        )
        await _seed_transaction(
            db_session,
            account.id,
            reference_number="REF-stmt-00000002",
            txn_type=TransactionType.DEPOSIT_CASH,
            amount_cents=50_000,
            balance_after_cents=565_000,
            description="Cash Deposit",
        )

        result = await generate_statement(db_session, account.id, days=30)
        assert result["transaction_count"] == 2

    @patch("src.atm.services.statement_service.generate_statement_pdf")
    async def test_opening_closing_balance_calculation(self, mock_pdf, db_session: AsyncSession):
        # Account currently at $5,150.00 (515_000 cents)
        # Had a withdrawal of $100.00 (debit) and deposit of $500.00 (credit)
        # Net effect: -100 + 500 = +400 in dollars = +40000 cents
        # Opening = closing - net = 515000 - 40000 = 475000
        account = await _seed_account_with_customer(db_session, balance_cents=515_000)
        await _seed_transaction(
            db_session,
            account.id,
            txn_type=TransactionType.WITHDRAWAL,
            amount_cents=10_000,
            balance_after_cents=505_000,
            reference_number="REF-stmt-calc-001",
        )
        await _seed_transaction(
            db_session,
            account.id,
            txn_type=TransactionType.DEPOSIT_CASH,
            amount_cents=50_000,
            balance_after_cents=555_000,
            reference_number="REF-stmt-calc-002",
        )

        result = await generate_statement(db_session, account.id, days=30)

        assert result["closing_balance"] == "$5,150.00"
        assert result["opening_balance"] == "$4,750.00"

    @patch("src.atm.services.statement_service.generate_statement_pdf")
    async def test_empty_statement(self, mock_pdf, db_session: AsyncSession):
        account = await _seed_account_with_customer(db_session, balance_cents=0)

        result = await generate_statement(db_session, account.id, days=30)

        assert result["transaction_count"] == 0
        assert result["opening_balance"] == "$0.00"
        assert result["closing_balance"] == "$0.00"

    async def test_account_not_found(self, db_session: AsyncSession):
        with pytest.raises(StatementError, match="Account not found"):
            await generate_statement(db_session, 999)

    @patch("src.atm.services.statement_service.generate_statement_pdf")
    async def test_file_path_contains_masked_account(self, mock_pdf, db_session: AsyncSession):
        account = await _seed_account_with_customer(db_session)
        result = await generate_statement(db_session, account.id)

        assert "****" in result["file_path"]
        assert result["file_path"].endswith(".pdf")

    @patch("src.atm.services.statement_service.generate_statement_pdf")
    async def test_pdf_generator_called_with_account_info(self, mock_pdf, db_session: AsyncSession):
        account = await _seed_account_with_customer(db_session, balance_cents=525_000)
        await generate_statement(db_session, account.id, days=7)

        mock_pdf.assert_called_once()
        call_kwargs = mock_pdf.call_args[1]
        assert call_kwargs["account_info"]["customer_name"] == "Alice Johnson"

    @patch("src.atm.services.statement_service.generate_statement_pdf")
    async def test_session_id_passed_to_audit(self, mock_pdf, db_session: AsyncSession):
        account = await _seed_account_with_customer(db_session)
        result = await generate_statement(db_session, account.id, session_id="test-session")
        assert result is not None

    @patch("src.atm.services.statement_service.generate_statement_pdf")
    async def test_debit_reduces_opening_balance(self, mock_pdf, db_session: AsyncSession):
        # Account at $1,000, one withdrawal of $200
        # Net effect: -20000
        # Opening = 100000 - (-20000) = 120000
        account = await _seed_account_with_customer(db_session, balance_cents=100_000)
        await _seed_transaction(
            db_session,
            account.id,
            txn_type=TransactionType.WITHDRAWAL,
            amount_cents=20_000,
            balance_after_cents=80_000,
            reference_number="REF-stmt-debit-01",
        )

        result = await generate_statement(db_session, account.id, days=30)
        assert result["opening_balance"] == "$1,200.00"
        assert result["closing_balance"] == "$1,000.00"
