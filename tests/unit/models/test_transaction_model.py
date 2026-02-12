"""Unit tests for Transaction model properties.

Coverage requirement: 100%

Tests: amount_dollars, is_debit, is_credit
"""

import pytest

from src.atm.models.transaction import Transaction, TransactionType


def _make_transaction(
    *,
    amount_cents: int = 10_000,
    transaction_type: TransactionType = TransactionType.WITHDRAWAL,
) -> Transaction:
    """Create a Transaction instance for property testing (no DB required)."""
    return Transaction(
        account_id=1,
        transaction_type=transaction_type,
        amount_cents=amount_cents,
        balance_after_cents=0,
        reference_number="REF-test-00000000",
        description="Test",
    )


class TestAmountDollars:
    def test_standard_amount(self):
        txn = _make_transaction(amount_cents=10_000)
        assert txn.amount_dollars == "$100.00"

    def test_zero_amount(self):
        txn = _make_transaction(amount_cents=0)
        assert txn.amount_dollars == "$0.00"

    def test_cents_only(self):
        txn = _make_transaction(amount_cents=99)
        assert txn.amount_dollars == "$0.99"

    def test_large_amount(self):
        txn = _make_transaction(amount_cents=99_999_999)
        assert txn.amount_dollars == "$999,999.99"

    def test_one_cent(self):
        txn = _make_transaction(amount_cents=1)
        assert txn.amount_dollars == "$0.01"


class TestIsDebit:
    def test_withdrawal_is_debit(self):
        txn = _make_transaction(transaction_type=TransactionType.WITHDRAWAL)
        assert txn.is_debit is True

    def test_transfer_out_is_debit(self):
        txn = _make_transaction(transaction_type=TransactionType.TRANSFER_OUT)
        assert txn.is_debit is True

    def test_fee_is_debit(self):
        txn = _make_transaction(transaction_type=TransactionType.FEE)
        assert txn.is_debit is True

    def test_deposit_cash_is_not_debit(self):
        txn = _make_transaction(transaction_type=TransactionType.DEPOSIT_CASH)
        assert txn.is_debit is False

    def test_deposit_check_is_not_debit(self):
        txn = _make_transaction(transaction_type=TransactionType.DEPOSIT_CHECK)
        assert txn.is_debit is False

    def test_transfer_in_is_not_debit(self):
        txn = _make_transaction(transaction_type=TransactionType.TRANSFER_IN)
        assert txn.is_debit is False

    def test_interest_is_not_debit(self):
        txn = _make_transaction(transaction_type=TransactionType.INTEREST)
        assert txn.is_debit is False


class TestIsCredit:
    def test_deposit_cash_is_credit(self):
        txn = _make_transaction(transaction_type=TransactionType.DEPOSIT_CASH)
        assert txn.is_credit is True

    def test_deposit_check_is_credit(self):
        txn = _make_transaction(transaction_type=TransactionType.DEPOSIT_CHECK)
        assert txn.is_credit is True

    def test_transfer_in_is_credit(self):
        txn = _make_transaction(transaction_type=TransactionType.TRANSFER_IN)
        assert txn.is_credit is True

    def test_interest_is_credit(self):
        txn = _make_transaction(transaction_type=TransactionType.INTEREST)
        assert txn.is_credit is True

    def test_withdrawal_is_not_credit(self):
        txn = _make_transaction(transaction_type=TransactionType.WITHDRAWAL)
        assert txn.is_credit is False

    def test_transfer_out_is_not_credit(self):
        txn = _make_transaction(transaction_type=TransactionType.TRANSFER_OUT)
        assert txn.is_credit is False

    def test_fee_is_not_credit(self):
        txn = _make_transaction(transaction_type=TransactionType.FEE)
        assert txn.is_credit is False
