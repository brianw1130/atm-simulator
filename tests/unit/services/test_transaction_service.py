"""Unit tests for transaction_service.

Coverage requirement: 100%

Tests:
    - _format_cents: various amounts
    - _next_business_day: weekdays, weekends, multi-day
    - _load_account: active, frozen, closed, not found
    - withdraw: valid, insufficient funds, daily limit, non-$20 multiple,
      zero/negative, frozen account, denomination breakdown
    - deposit: cash small (no hold), cash large (hold), check small, check large,
      invalid type, zero/negative, check without number, frozen account
    - transfer: valid own-account, valid external, insufficient funds, daily limit,
      destination not found, self-transfer, inactive dest, zero/negative, frozen source
"""

from datetime import UTC, date, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.atm.models.account import Account, AccountStatus, AccountType
from src.atm.models.customer import Customer
from src.atm.models.transaction import Transaction, TransactionType
from src.atm.services.transaction_service import (
    AccountFrozenError,
    DailyLimitExceededError,
    InsufficientFundsError,
    TransactionError,
    _format_cents,
    _next_business_day,
    deposit,
    transfer,
    withdraw,
)

pytestmark = pytest.mark.asyncio


async def _seed_account(
    db_session: AsyncSession,
    *,
    account_number: str = "1000-0001-0001",
    balance_cents: int = 525_000,
    available_balance_cents: int | None = None,
    daily_withdrawal_used_cents: int = 0,
    daily_transfer_used_cents: int = 0,
    status: AccountStatus = AccountStatus.ACTIVE,
    account_type: AccountType = AccountType.CHECKING,
) -> Account:
    if available_balance_cents is None:
        available_balance_cents = balance_cents
    customer = Customer(
        first_name="Test",
        last_name="User",
        date_of_birth=date(1990, 1, 15),
        email=f"test-{account_number}@example.com",
    )
    db_session.add(customer)
    await db_session.flush()
    account = Account(
        customer_id=customer.id,
        account_number=account_number,
        account_type=account_type,
        balance_cents=balance_cents,
        available_balance_cents=available_balance_cents,
        daily_withdrawal_used_cents=daily_withdrawal_used_cents,
        daily_transfer_used_cents=daily_transfer_used_cents,
        status=status,
    )
    db_session.add(account)
    await db_session.flush()
    return account


# ── _format_cents ────────────────────────────────────────────────────────────


class TestFormatCents:
    def test_zero(self):
        assert _format_cents(0) == "$0.00"

    def test_standard(self):
        assert _format_cents(10_000) == "$100.00"

    def test_large(self):
        assert _format_cents(99_999_999) == "$999,999.99"


# ── _next_business_day ───────────────────────────────────────────────────────


class TestNextBusinessDay:
    def test_monday_plus_one(self):
        # 2026-02-09 is a Monday
        monday = datetime(2026, 2, 9, 12, 0, tzinfo=UTC)
        result = _next_business_day(monday, days=1)
        assert result.weekday() == 1  # Tuesday

    def test_friday_plus_one_skips_weekend(self):
        # 2026-02-13 is a Friday
        friday = datetime(2026, 2, 13, 12, 0, tzinfo=UTC)
        result = _next_business_day(friday, days=1)
        assert result.weekday() == 0  # Monday
        assert result.day == 16

    def test_friday_plus_two(self):
        friday = datetime(2026, 2, 13, 12, 0, tzinfo=UTC)
        result = _next_business_day(friday, days=2)
        assert result.weekday() == 1  # Tuesday
        assert result.day == 17

    def test_saturday_plus_one(self):
        saturday = datetime(2026, 2, 14, 12, 0, tzinfo=UTC)
        result = _next_business_day(saturday, days=1)
        assert result.weekday() == 0  # Monday

    def test_preserves_time(self):
        monday = datetime(2026, 2, 9, 15, 30, 45, tzinfo=UTC)
        result = _next_business_day(monday, days=1)
        assert result.hour == 15
        assert result.minute == 30

    def test_wednesday_plus_three(self):
        wednesday = datetime(2026, 2, 11, 12, 0, tzinfo=UTC)
        result = _next_business_day(wednesday, days=3)
        assert result.weekday() == 0  # Monday
        assert result.day == 16


# ── withdraw ─────────────────────────────────────────────────────────────────


class TestWithdraw:
    async def test_successful_withdrawal(self, db_session: AsyncSession):
        account = await _seed_account(db_session, balance_cents=525_000)
        result = await withdraw(db_session, account.id, 10_000)

        assert result["transaction_type"] == "WITHDRAWAL"
        assert result["amount"] == "$100.00"
        assert result["balance_after"] == "$5,150.00"
        assert result["reference_number"].startswith("REF-")
        assert "successful" in result["message"]

    async def test_denomination_breakdown(self, db_session: AsyncSession):
        account = await _seed_account(db_session)
        result = await withdraw(db_session, account.id, 10_000)

        denoms = result["denominations"]
        assert denoms["twenties"] == 5
        assert denoms["total_bills"] == 5
        assert denoms["total_amount"] == "$100.00"

    async def test_balance_updated(self, db_session: AsyncSession):
        account = await _seed_account(db_session, balance_cents=525_000)
        await withdraw(db_session, account.id, 10_000)

        await db_session.refresh(account)
        assert account.balance_cents == 515_000
        assert account.available_balance_cents == 515_000

    async def test_daily_usage_tracked(self, db_session: AsyncSession):
        account = await _seed_account(db_session)
        await withdraw(db_session, account.id, 10_000)

        await db_session.refresh(account)
        assert account.daily_withdrawal_used_cents == 10_000

    async def test_transaction_record_created(self, db_session: AsyncSession):
        account = await _seed_account(db_session)
        result = await withdraw(db_session, account.id, 10_000)

        stmt = select(Transaction).where(Transaction.reference_number == result["reference_number"])
        txn_result = await db_session.execute(stmt)
        txn = txn_result.scalars().first()
        assert txn is not None
        assert txn.transaction_type == TransactionType.WITHDRAWAL
        assert txn.amount_cents == 10_000

    async def test_insufficient_funds(self, db_session: AsyncSession):
        account = await _seed_account(db_session, balance_cents=5_000)
        with pytest.raises(InsufficientFundsError, match="Insufficient funds"):
            await withdraw(db_session, account.id, 10_000)

    async def test_daily_limit_exceeded(self, db_session: AsyncSession):
        account = await _seed_account(
            db_session,
            balance_cents=1_000_000,
            daily_withdrawal_used_cents=48_000,
        )
        with pytest.raises(DailyLimitExceededError, match="Daily withdrawal limit"):
            await withdraw(db_session, account.id, 4_000)

    async def test_non_multiple_of_20_rejected(self, db_session: AsyncSession):
        account = await _seed_account(db_session)
        with pytest.raises(TransactionError, match="multiple of \\$20"):
            await withdraw(db_session, account.id, 5_500)

    async def test_zero_amount_rejected(self, db_session: AsyncSession):
        account = await _seed_account(db_session)
        with pytest.raises(TransactionError, match="positive"):
            await withdraw(db_session, account.id, 0)

    async def test_negative_amount_rejected(self, db_session: AsyncSession):
        account = await _seed_account(db_session)
        with pytest.raises(TransactionError, match="positive"):
            await withdraw(db_session, account.id, -2_000)

    async def test_frozen_account_rejected(self, db_session: AsyncSession):
        account = await _seed_account(db_session, status=AccountStatus.FROZEN)
        with pytest.raises(AccountFrozenError, match="frozen"):
            await withdraw(db_session, account.id, 2_000)

    async def test_closed_account_rejected(self, db_session: AsyncSession):
        account = await _seed_account(db_session, status=AccountStatus.CLOSED)
        with pytest.raises(AccountFrozenError, match="closed"):
            await withdraw(db_session, account.id, 2_000)

    async def test_account_not_found(self, db_session: AsyncSession):
        with pytest.raises(TransactionError, match="Account not found"):
            await withdraw(db_session, 999, 2_000)


# ── deposit ──────────────────────────────────────────────────────────────────


class TestDeposit:
    async def test_cash_small_no_hold(self, db_session: AsyncSession):
        account = await _seed_account(db_session, balance_cents=100_000)
        result = await deposit(db_session, account.id, 15_000, "cash")

        assert result["transaction_type"] == "DEPOSIT_CASH"
        assert result["available_immediately"] == "$150.00"
        assert result["held_amount"] == "$0.00"
        assert result["hold_until"] is None

        await db_session.refresh(account)
        assert account.balance_cents == 115_000
        assert account.available_balance_cents == 115_000

    async def test_cash_large_partial_hold(self, db_session: AsyncSession):
        account = await _seed_account(db_session, balance_cents=100_000)
        result = await deposit(db_session, account.id, 50_000, "cash")

        assert result["available_immediately"] == "$200.00"
        assert result["held_amount"] == "$300.00"
        assert result["hold_until"] is not None

        await db_session.refresh(account)
        assert account.balance_cents == 150_000
        assert account.available_balance_cents == 120_000

    async def test_cash_exactly_200_no_hold(self, db_session: AsyncSession):
        account = await _seed_account(db_session, balance_cents=100_000)
        result = await deposit(db_session, account.id, 20_000, "cash")

        assert result["available_immediately"] == "$200.00"
        assert result["held_amount"] == "$0.00"
        assert result["hold_until"] is None

    async def test_check_small_all_held(self, db_session: AsyncSession):
        account = await _seed_account(db_session, balance_cents=100_000)
        result = await deposit(db_session, account.id, 15_000, "check", check_number="4521")

        assert result["transaction_type"] == "DEPOSIT_CHECK"
        assert result["available_immediately"] == "$0.00"
        assert result["held_amount"] == "$150.00"
        assert result["hold_until"] is not None

        await db_session.refresh(account)
        assert account.balance_cents == 115_000
        assert account.available_balance_cents == 100_000

    async def test_check_large_all_held(self, db_session: AsyncSession):
        account = await _seed_account(db_session, balance_cents=100_000)
        result = await deposit(db_session, account.id, 100_000, "check", check_number="9999")

        assert result["available_immediately"] == "$0.00"
        assert result["held_amount"] == "$1,000.00"
        assert result["hold_until"] is not None

    async def test_invalid_deposit_type(self, db_session: AsyncSession):
        account = await _seed_account(db_session)
        with pytest.raises(TransactionError, match="deposit_type"):
            await deposit(db_session, account.id, 10_000, "wire")

    async def test_zero_amount_rejected(self, db_session: AsyncSession):
        account = await _seed_account(db_session)
        with pytest.raises(TransactionError, match="positive"):
            await deposit(db_session, account.id, 0, "cash")

    async def test_negative_amount_rejected(self, db_session: AsyncSession):
        account = await _seed_account(db_session)
        with pytest.raises(TransactionError, match="positive"):
            await deposit(db_session, account.id, -100, "cash")

    async def test_check_without_number_rejected(self, db_session: AsyncSession):
        account = await _seed_account(db_session)
        with pytest.raises(TransactionError, match="Check number"):
            await deposit(db_session, account.id, 10_000, "check")

    async def test_frozen_account_rejected(self, db_session: AsyncSession):
        account = await _seed_account(db_session, status=AccountStatus.FROZEN)
        with pytest.raises(AccountFrozenError):
            await deposit(db_session, account.id, 10_000, "cash")

    async def test_account_not_found(self, db_session: AsyncSession):
        with pytest.raises(TransactionError, match="Account not found"):
            await deposit(db_session, 999, 10_000, "cash")

    async def test_transaction_record_created(self, db_session: AsyncSession):
        account = await _seed_account(db_session)
        result = await deposit(db_session, account.id, 15_000, "cash")

        stmt = select(Transaction).where(Transaction.reference_number == result["reference_number"])
        txn_result = await db_session.execute(stmt)
        txn = txn_result.scalars().first()
        assert txn is not None
        assert txn.transaction_type == TransactionType.DEPOSIT_CASH
        assert txn.amount_cents == 15_000

    async def test_check_deposit_stores_check_number(self, db_session: AsyncSession):
        account = await _seed_account(db_session)
        result = await deposit(db_session, account.id, 10_000, "check", check_number="CHK-123")

        stmt = select(Transaction).where(Transaction.reference_number == result["reference_number"])
        txn_result = await db_session.execute(stmt)
        txn = txn_result.scalars().first()
        assert txn.check_number == "CHK-123"

    async def test_check_description_includes_check_number(self, db_session: AsyncSession):
        account = await _seed_account(db_session)
        result = await deposit(db_session, account.id, 10_000, "check", check_number="4521")

        stmt = select(Transaction).where(Transaction.reference_number == result["reference_number"])
        txn_result = await db_session.execute(stmt)
        txn = txn_result.scalars().first()
        assert "4521" in txn.description


# ── transfer ─────────────────────────────────────────────────────────────────


class TestTransfer:
    async def test_successful_own_account_transfer(self, db_session: AsyncSession):
        source = await _seed_account(
            db_session, account_number="1000-0001-0001", balance_cents=525_000
        )
        await _seed_account(
            db_session,
            account_number="1000-0001-0002",
            balance_cents=1_250_000,
            account_type=AccountType.SAVINGS,
        )

        result = await transfer(db_session, source.id, "1000-0001-0002", 100_000)

        assert result["transaction_type"] == "TRANSFER_OUT"
        assert result["amount"] == "$1,000.00"
        assert result["balance_after"] == "$4,250.00"
        assert "****" in result["source_account"]
        assert "****" in result["destination_account"]

    async def test_source_balance_decreases(self, db_session: AsyncSession):
        source = await _seed_account(
            db_session, account_number="1000-0001-0001", balance_cents=525_000
        )
        await _seed_account(db_session, account_number="1000-0001-0002", balance_cents=0)

        await transfer(db_session, source.id, "1000-0001-0002", 100_000)

        await db_session.refresh(source)
        assert source.balance_cents == 425_000
        assert source.available_balance_cents == 425_000

    async def test_dest_balance_increases(self, db_session: AsyncSession):
        source = await _seed_account(
            db_session, account_number="1000-0001-0001", balance_cents=525_000
        )
        dest = await _seed_account(
            db_session, account_number="1000-0001-0002", balance_cents=100_000
        )

        await transfer(db_session, source.id, "1000-0001-0002", 50_000)

        await db_session.refresh(dest)
        assert dest.balance_cents == 150_000

    async def test_daily_transfer_usage_tracked(self, db_session: AsyncSession):
        source = await _seed_account(
            db_session, account_number="1000-0001-0001", balance_cents=525_000
        )
        await _seed_account(db_session, account_number="1000-0001-0002", balance_cents=0)

        await transfer(db_session, source.id, "1000-0001-0002", 50_000)

        await db_session.refresh(source)
        assert source.daily_transfer_used_cents == 50_000

    async def test_two_transaction_records_created(self, db_session: AsyncSession):
        source = await _seed_account(
            db_session, account_number="1000-0001-0001", balance_cents=525_000
        )
        dest = await _seed_account(db_session, account_number="1000-0001-0002", balance_cents=0)

        await transfer(db_session, source.id, "1000-0001-0002", 50_000)

        stmt = select(Transaction).where(Transaction.account_id == source.id)
        txn_result = await db_session.execute(stmt)
        source_txns = list(txn_result.scalars().all())
        assert len(source_txns) == 1
        assert source_txns[0].transaction_type == TransactionType.TRANSFER_OUT
        assert source_txns[0].related_account_id == dest.id

        stmt2 = select(Transaction).where(Transaction.account_id == dest.id)
        txn_result2 = await db_session.execute(stmt2)
        dest_txns = list(txn_result2.scalars().all())
        assert len(dest_txns) == 1
        assert dest_txns[0].transaction_type == TransactionType.TRANSFER_IN
        assert dest_txns[0].related_account_id == source.id

    async def test_insufficient_funds(self, db_session: AsyncSession):
        source = await _seed_account(
            db_session, account_number="1000-0001-0001", balance_cents=5_000
        )
        await _seed_account(db_session, account_number="1000-0001-0002", balance_cents=0)

        with pytest.raises(InsufficientFundsError, match="Insufficient funds"):
            await transfer(db_session, source.id, "1000-0001-0002", 50_000)

    async def test_daily_limit_exceeded(self, db_session: AsyncSession):
        source = await _seed_account(
            db_session,
            account_number="1000-0001-0001",
            balance_cents=10_000_000,
            daily_transfer_used_cents=240_000,
        )
        await _seed_account(db_session, account_number="1000-0001-0002", balance_cents=0)

        with pytest.raises(DailyLimitExceededError, match="Daily transfer limit"):
            await transfer(db_session, source.id, "1000-0001-0002", 20_000)

    async def test_destination_not_found(self, db_session: AsyncSession):
        source = await _seed_account(
            db_session, account_number="1000-0001-0001", balance_cents=525_000
        )
        with pytest.raises(TransactionError, match="Destination account not found"):
            await transfer(db_session, source.id, "9999-9999-9999", 10_000)

    async def test_self_transfer_rejected(self, db_session: AsyncSession):
        source = await _seed_account(
            db_session, account_number="1000-0001-0001", balance_cents=525_000
        )
        with pytest.raises(TransactionError, match="same account"):
            await transfer(db_session, source.id, "1000-0001-0001", 10_000)

    async def test_inactive_destination_rejected(self, db_session: AsyncSession):
        source = await _seed_account(
            db_session, account_number="1000-0001-0001", balance_cents=525_000
        )
        await _seed_account(
            db_session,
            account_number="1000-0001-0002",
            status=AccountStatus.FROZEN,
        )

        with pytest.raises(TransactionError, match="not active"):
            await transfer(db_session, source.id, "1000-0001-0002", 10_000)

    async def test_closed_destination_rejected(self, db_session: AsyncSession):
        source = await _seed_account(
            db_session, account_number="1000-0001-0001", balance_cents=525_000
        )
        await _seed_account(
            db_session,
            account_number="1000-0001-0002",
            status=AccountStatus.CLOSED,
        )

        with pytest.raises(TransactionError, match="not active"):
            await transfer(db_session, source.id, "1000-0001-0002", 10_000)

    async def test_zero_amount_rejected(self, db_session: AsyncSession):
        source = await _seed_account(
            db_session, account_number="1000-0001-0001", balance_cents=525_000
        )
        with pytest.raises(TransactionError, match="positive"):
            await transfer(db_session, source.id, "1000-0001-0002", 0)

    async def test_negative_amount_rejected(self, db_session: AsyncSession):
        source = await _seed_account(
            db_session, account_number="1000-0001-0001", balance_cents=525_000
        )
        with pytest.raises(TransactionError, match="positive"):
            await transfer(db_session, source.id, "1000-0001-0002", -1)

    async def test_frozen_source_rejected(self, db_session: AsyncSession):
        source = await _seed_account(
            db_session,
            account_number="1000-0001-0001",
            balance_cents=525_000,
            status=AccountStatus.FROZEN,
        )
        await _seed_account(db_session, account_number="1000-0001-0002", balance_cents=0)

        with pytest.raises(AccountFrozenError):
            await transfer(db_session, source.id, "1000-0001-0002", 10_000)

    async def test_source_not_found(self, db_session: AsyncSession):
        with pytest.raises(TransactionError, match="Account not found"):
            await transfer(db_session, 999, "1000-0001-0002", 10_000)
