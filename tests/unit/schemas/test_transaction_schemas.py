"""Unit tests for transaction Pydantic schemas.

Coverage requirement: 100%

Tests WithdrawalRequest, DepositRequest, TransferRequest, StatementRequest,
and response schemas from src/atm/schemas/transaction.py.
"""

from datetime import date, datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from src.atm.schemas.transaction import (
    DenominationBreakdown,
    DepositRequest,
    DepositResponse,
    ErrorResponse,
    StatementRequest,
    StatementResponse,
    TransactionResponse,
    TransferRequest,
    TransferResponse,
    WithdrawalRequest,
    WithdrawalResponse,
)


# ── WithdrawalRequest ────────────────────────────────────────────────────────


class TestWithdrawalRequest:
    @pytest.mark.parametrize("cents", [2000, 4000, 6000, 10000, 20000])
    def test_valid_multiples_of_2000(self, cents):
        req = WithdrawalRequest(amount_cents=cents)
        assert req.amount_cents == cents

    def test_reject_5500_not_multiple(self):
        with pytest.raises(ValidationError) as exc_info:
            WithdrawalRequest(amount_cents=5500)
        assert "multiple of $20" in str(exc_info.value)

    def test_reject_1000_not_multiple(self):
        with pytest.raises(ValidationError):
            WithdrawalRequest(amount_cents=1000)

    def test_reject_100_not_multiple(self):
        with pytest.raises(ValidationError):
            WithdrawalRequest(amount_cents=100)

    def test_reject_zero(self):
        with pytest.raises(ValidationError):
            WithdrawalRequest(amount_cents=0)

    def test_reject_negative(self):
        with pytest.raises(ValidationError):
            WithdrawalRequest(amount_cents=-2000)

    def test_reject_odd_large_amount(self):
        with pytest.raises(ValidationError):
            WithdrawalRequest(amount_cents=2001)

    def test_large_valid_amount(self):
        req = WithdrawalRequest(amount_cents=100000)
        assert req.amount_cents == 100000


# ── DepositRequest ───────────────────────────────────────────────────────────


class TestDepositRequest:
    def test_valid_cash_deposit(self):
        req = DepositRequest(amount_cents=50000, deposit_type="cash")
        assert req.amount_cents == 50000
        assert req.deposit_type == "cash"
        assert req.check_number is None

    def test_valid_check_deposit_with_check_number(self):
        req = DepositRequest(
            amount_cents=100000, deposit_type="check", check_number="4521"
        )
        assert req.deposit_type == "check"
        assert req.check_number == "4521"

    def test_check_deposit_with_explicit_none_check_number_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            DepositRequest(
                amount_cents=100000, deposit_type="check", check_number=None
            )
        assert "Check number is required" in str(exc_info.value)

    def test_check_deposit_with_empty_check_number_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            DepositRequest(
                amount_cents=100000, deposit_type="check", check_number=""
            )
        assert "Check number is required" in str(exc_info.value)

    def test_cash_deposit_without_check_number_accepted(self):
        req = DepositRequest(amount_cents=5000, deposit_type="cash")
        assert req.check_number is None

    def test_invalid_deposit_type_rejected(self):
        with pytest.raises(ValidationError):
            DepositRequest(amount_cents=5000, deposit_type="wire")

    def test_zero_amount_rejected(self):
        with pytest.raises(ValidationError):
            DepositRequest(amount_cents=0, deposit_type="cash")

    def test_negative_amount_rejected(self):
        with pytest.raises(ValidationError):
            DepositRequest(amount_cents=-100, deposit_type="cash")

    def test_check_number_too_long_rejected(self):
        with pytest.raises(ValidationError):
            DepositRequest(
                amount_cents=5000, deposit_type="check", check_number="A" * 21
            )


# ── TransferRequest ──────────────────────────────────────────────────────────


class TestTransferRequest:
    def test_valid_transfer(self):
        req = TransferRequest(
            destination_account_number="1000-0002-0001", amount_cents=100000
        )
        assert req.destination_account_number == "1000-0002-0001"
        assert req.amount_cents == 100000

    def test_empty_destination_rejected(self):
        with pytest.raises(ValidationError):
            TransferRequest(destination_account_number="", amount_cents=100000)

    def test_destination_too_long_rejected(self):
        with pytest.raises(ValidationError):
            TransferRequest(
                destination_account_number="A" * 21, amount_cents=100000
            )

    def test_zero_amount_rejected(self):
        with pytest.raises(ValidationError):
            TransferRequest(
                destination_account_number="1000-0002-0001", amount_cents=0
            )

    def test_negative_amount_rejected(self):
        with pytest.raises(ValidationError):
            TransferRequest(
                destination_account_number="1000-0002-0001", amount_cents=-5000
            )

    def test_small_valid_amount(self):
        req = TransferRequest(
            destination_account_number="1000-0002-0001", amount_cents=1
        )
        assert req.amount_cents == 1


# ── StatementRequest ─────────────────────────────────────────────────────────


class TestStatementRequest:
    def test_default_days(self):
        req = StatementRequest()
        assert req.days == 30
        assert req.start_date is None
        assert req.end_date is None

    def test_valid_days_7(self):
        req = StatementRequest(days=7)
        assert req.days == 7

    def test_valid_days_90(self):
        req = StatementRequest(days=90)
        assert req.days == 90

    def test_valid_days_365(self):
        req = StatementRequest(days=365)
        assert req.days == 365

    def test_days_zero_rejected(self):
        with pytest.raises(ValidationError):
            StatementRequest(days=0)

    def test_days_negative_rejected(self):
        with pytest.raises(ValidationError):
            StatementRequest(days=-1)

    def test_days_over_365_rejected(self):
        with pytest.raises(ValidationError):
            StatementRequest(days=366)

    def test_valid_date_range(self):
        today = date.today()
        start = today - timedelta(days=30)
        req = StatementRequest(start_date=start, end_date=today)
        assert req.start_date == start
        assert req.end_date == today

    def test_end_before_start_rejected(self):
        today = date.today()
        with pytest.raises(ValidationError) as exc_info:
            StatementRequest(
                start_date=today, end_date=today - timedelta(days=10)
            )
        assert "end_date must not be before start_date" in str(exc_info.value)

    def test_future_end_date_rejected(self):
        today = date.today()
        with pytest.raises(ValidationError) as exc_info:
            StatementRequest(
                start_date=today,
                end_date=today + timedelta(days=10),
            )
        assert "future" in str(exc_info.value)

    def test_start_date_without_end_date_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            StatementRequest(start_date=date.today() - timedelta(days=10))
        assert "Both start_date and end_date" in str(exc_info.value)

    def test_end_date_without_start_date_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            StatementRequest(end_date=date.today())
        assert "Both start_date and end_date" in str(exc_info.value)

    def test_same_start_and_end_accepted(self):
        today = date.today()
        req = StatementRequest(start_date=today, end_date=today)
        assert req.start_date == req.end_date


# ── Response Schemas ─────────────────────────────────────────────────────────


class TestTransactionResponse:
    def test_creation(self):
        resp = TransactionResponse(
            reference_number="REF-abc-12345678",
            transaction_type="WITHDRAWAL",
            amount="$100.00",
            balance_after="$5,150.00",
            message="Withdrawal successful",
        )
        assert resp.reference_number == "REF-abc-12345678"
        assert resp.transaction_type == "WITHDRAWAL"


class TestErrorResponse:
    def test_creation(self):
        resp = ErrorResponse(
            error="insufficient_funds",
            detail="Your account does not have enough funds.",
            error_code="ERR_INSUFFICIENT_FUNDS",
        )
        assert resp.error == "insufficient_funds"
        assert resp.error_code == "ERR_INSUFFICIENT_FUNDS"


class TestDenominationBreakdown:
    def test_creation(self):
        breakdown = DenominationBreakdown(
            twenties=5, total_bills=5, total_amount="$100.00"
        )
        assert breakdown.twenties == 5
        assert breakdown.total_bills == 5

    def test_zero_bills(self):
        breakdown = DenominationBreakdown(
            twenties=0, total_bills=0, total_amount="$0.00"
        )
        assert breakdown.twenties == 0


class TestWithdrawalResponse:
    def test_creation(self):
        resp = WithdrawalResponse(
            reference_number="REF-abc-12345678",
            transaction_type="WITHDRAWAL",
            amount="$100.00",
            balance_after="$5,150.00",
            message="Withdrawal successful",
            denominations=DenominationBreakdown(
                twenties=5, total_bills=5, total_amount="$100.00"
            ),
        )
        assert resp.denominations.twenties == 5


class TestDepositResponse:
    def test_creation_with_hold(self):
        hold_time = datetime.now(tz=timezone.utc) + timedelta(days=1)
        resp = DepositResponse(
            reference_number="REF-abc-12345678",
            transaction_type="DEPOSIT_CASH",
            amount="$500.00",
            balance_after="$5,750.00",
            message="Deposit successful",
            available_immediately="$200.00",
            held_amount="$300.00",
            hold_until=hold_time,
        )
        assert resp.available_immediately == "$200.00"
        assert resp.hold_until == hold_time

    def test_creation_without_hold(self):
        resp = DepositResponse(
            reference_number="REF-abc-12345678",
            transaction_type="DEPOSIT_CASH",
            amount="$150.00",
            balance_after="$5,400.00",
            message="Deposit successful",
            available_immediately="$150.00",
            held_amount="$0.00",
            hold_until=None,
        )
        assert resp.hold_until is None


class TestTransferResponse:
    def test_creation(self):
        resp = TransferResponse(
            reference_number="REF-abc-12345678",
            transaction_type="TRANSFER_OUT",
            amount="$200.00",
            balance_after="$5,050.00",
            message="Transfer successful",
            source_account="****-****-0001",
            destination_account="****-****-0002",
        )
        assert resp.source_account == "****-****-0001"
        assert resp.destination_account == "****-****-0002"


class TestStatementResponse:
    def test_creation(self):
        resp = StatementResponse(
            file_path="/app/statements/stmt_20240101.pdf",
            period="2024-01-01 to 2024-01-31",
            transaction_count=15,
            opening_balance="$5,000.00",
            closing_balance="$5,250.00",
        )
        assert resp.transaction_count == 15
        assert resp.file_path.endswith(".pdf")
