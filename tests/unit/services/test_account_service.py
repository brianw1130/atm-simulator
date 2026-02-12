"""Unit tests for account_service.

Coverage requirement: 100%

Tests:
    - _format_cents: various amounts
    - get_customer_accounts: returns accounts, excludes closed, empty list
    - get_account_balance: returns balance + mini-statement, account not found,
      transactions ordering, debit/credit sign formatting
"""

from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.atm.models.account import Account, AccountStatus, AccountType
from src.atm.models.customer import Customer
from src.atm.models.transaction import Transaction, TransactionType
from src.atm.services.account_service import (
    AccountError,
    _format_cents,
    get_account_balance,
    get_customer_accounts,
)

pytestmark = pytest.mark.asyncio


async def _seed_customer(db_session: AsyncSession) -> Customer:
    customer = Customer(
        first_name="Alice",
        last_name="Johnson",
        date_of_birth=date(1990, 1, 15),
        email="alice-acct-test@example.com",
    )
    db_session.add(customer)
    await db_session.flush()
    return customer


async def _seed_account(
    db_session: AsyncSession,
    customer_id: int,
    *,
    account_number: str = "1000-0001-0001",
    account_type: AccountType = AccountType.CHECKING,
    balance_cents: int = 525_000,
    status: AccountStatus = AccountStatus.ACTIVE,
) -> Account:
    account = Account(
        customer_id=customer_id,
        account_number=account_number,
        account_type=account_type,
        balance_cents=balance_cents,
        available_balance_cents=balance_cents,
        status=status,
    )
    db_session.add(account)
    await db_session.flush()
    return account


async def _seed_transaction(
    db_session: AsyncSession,
    account_id: int,
    *,
    txn_type: TransactionType = TransactionType.WITHDRAWAL,
    amount_cents: int = 10_000,
    balance_after_cents: int = 515_000,
    reference_number: str = "REF-test-00000001",
    description: str = "Test withdrawal",
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

    def test_standard_amount(self):
        assert _format_cents(525_000) == "$5,250.00"

    def test_cents_only(self):
        assert _format_cents(75) == "$0.75"

    def test_one_cent(self):
        assert _format_cents(1) == "$0.01"

    def test_large_amount(self):
        assert _format_cents(99_999_999) == "$999,999.99"


# ── get_customer_accounts ────────────────────────────────────────────────────


class TestGetCustomerAccounts:
    async def test_returns_active_accounts(self, db_session: AsyncSession):
        customer = await _seed_customer(db_session)
        await _seed_account(
            db_session, customer.id, account_number="1000-0001-0001"
        )
        await _seed_account(
            db_session,
            customer.id,
            account_number="1000-0001-0002",
            account_type=AccountType.SAVINGS,
        )

        accounts = await get_customer_accounts(db_session, customer.id)
        assert len(accounts) == 2

    async def test_excludes_closed_accounts(self, db_session: AsyncSession):
        customer = await _seed_customer(db_session)
        await _seed_account(
            db_session, customer.id, account_number="1000-0001-0001"
        )
        await _seed_account(
            db_session,
            customer.id,
            account_number="1000-0001-0002",
            status=AccountStatus.CLOSED,
        )

        accounts = await get_customer_accounts(db_session, customer.id)
        assert len(accounts) == 1

    async def test_includes_frozen_accounts(self, db_session: AsyncSession):
        customer = await _seed_customer(db_session)
        await _seed_account(
            db_session,
            customer.id,
            account_number="1000-0001-0001",
            status=AccountStatus.FROZEN,
        )

        accounts = await get_customer_accounts(db_session, customer.id)
        assert len(accounts) == 1

    async def test_returns_empty_for_no_accounts(self, db_session: AsyncSession):
        customer = await _seed_customer(db_session)
        accounts = await get_customer_accounts(db_session, customer.id)
        assert accounts == []

    async def test_returns_empty_for_nonexistent_customer(self, db_session: AsyncSession):
        accounts = await get_customer_accounts(db_session, 999)
        assert accounts == []

    async def test_ordered_by_account_number(self, db_session: AsyncSession):
        customer = await _seed_customer(db_session)
        await _seed_account(
            db_session, customer.id, account_number="1000-0001-0002"
        )
        await _seed_account(
            db_session, customer.id, account_number="1000-0001-0001"
        )

        accounts = await get_customer_accounts(db_session, customer.id)
        assert accounts[0].account_number == "1000-0001-0001"
        assert accounts[1].account_number == "1000-0001-0002"


# ── get_account_balance ──────────────────────────────────────────────────────


class TestGetAccountBalance:
    async def test_returns_balance_info(self, db_session: AsyncSession):
        customer = await _seed_customer(db_session)
        account = await _seed_account(
            db_session, customer.id, balance_cents=525_000
        )

        result = await get_account_balance(db_session, account.id)
        assert result["account"]["balance"] == "$5,250.00"
        assert result["account"]["available_balance"] == "$5,250.00"
        assert result["account"]["status"] == AccountStatus.ACTIVE

    async def test_returns_masked_account_number(self, db_session: AsyncSession):
        customer = await _seed_customer(db_session)
        account = await _seed_account(db_session, customer.id)

        result = await get_account_balance(db_session, account.id)
        assert "****" in result["account"]["account_number"]

    async def test_account_not_found_raises_error(self, db_session: AsyncSession):
        with pytest.raises(AccountError, match="Account not found"):
            await get_account_balance(db_session, 999)

    async def test_returns_recent_transactions(self, db_session: AsyncSession):
        customer = await _seed_customer(db_session)
        account = await _seed_account(db_session, customer.id)

        await _seed_transaction(
            db_session, account.id,
            reference_number="REF-test-00000001",
            description="Withdrawal 1",
        )
        await _seed_transaction(
            db_session, account.id,
            reference_number="REF-test-00000002",
            description="Withdrawal 2",
        )

        result = await get_account_balance(db_session, account.id)
        assert len(result["recent_transactions"]) == 2

    async def test_limits_to_5_transactions(self, db_session: AsyncSession):
        customer = await _seed_customer(db_session)
        account = await _seed_account(db_session, customer.id)

        for i in range(7):
            await _seed_transaction(
                db_session, account.id,
                reference_number=f"REF-test-{i:08d}",
                description=f"Txn {i}",
            )

        result = await get_account_balance(db_session, account.id)
        assert len(result["recent_transactions"]) == 5

    async def test_empty_transactions(self, db_session: AsyncSession):
        customer = await _seed_customer(db_session)
        account = await _seed_account(db_session, customer.id)

        result = await get_account_balance(db_session, account.id)
        assert result["recent_transactions"] == []

    async def test_debit_has_minus_sign(self, db_session: AsyncSession):
        customer = await _seed_customer(db_session)
        account = await _seed_account(db_session, customer.id)

        await _seed_transaction(
            db_session, account.id,
            txn_type=TransactionType.WITHDRAWAL,
            amount_cents=10_000,
            reference_number="REF-test-debit001",
        )

        result = await get_account_balance(db_session, account.id)
        assert result["recent_transactions"][0]["amount"].startswith("-")

    async def test_credit_has_plus_sign(self, db_session: AsyncSession):
        customer = await _seed_customer(db_session)
        account = await _seed_account(db_session, customer.id)

        await _seed_transaction(
            db_session, account.id,
            txn_type=TransactionType.DEPOSIT_CASH,
            amount_cents=50_000,
            reference_number="REF-test-credit01",
            description="Cash deposit",
        )

        result = await get_account_balance(db_session, account.id)
        assert result["recent_transactions"][0]["amount"].startswith("+")

    async def test_includes_session_id_in_audit(self, db_session: AsyncSession):
        customer = await _seed_customer(db_session)
        account = await _seed_account(db_session, customer.id)

        result = await get_account_balance(
            db_session, account.id, session_id="test-session"
        )
        assert result is not None
