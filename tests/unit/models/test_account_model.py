"""Unit tests for Account model properties and validators.

Coverage requirement: 100%

Tests: balance_dollars, available_balance_dollars, masked_account_number, is_active
"""

from src.atm.models.account import Account, AccountStatus, AccountType


def _make_account(
    *,
    balance_cents: int = 525_000,
    available_balance_cents: int = 525_000,
    account_number: str = "1000-0001-0001",
    status: AccountStatus = AccountStatus.ACTIVE,
) -> Account:
    """Create an Account instance for property testing (no DB required)."""
    return Account(
        customer_id=1,
        account_number=account_number,
        account_type=AccountType.CHECKING,
        balance_cents=balance_cents,
        available_balance_cents=available_balance_cents,
        status=status,
    )


class TestBalanceDollars:
    def test_standard_balance(self):
        account = _make_account(balance_cents=525_000)
        assert account.balance_dollars == "$5,250.00"

    def test_zero_balance(self):
        account = _make_account(balance_cents=0)
        assert account.balance_dollars == "$0.00"

    def test_cents_only(self):
        account = _make_account(balance_cents=75)
        assert account.balance_dollars == "$0.75"

    def test_large_balance(self):
        account = _make_account(balance_cents=99_999_999)
        assert account.balance_dollars == "$999,999.99"

    def test_one_cent(self):
        account = _make_account(balance_cents=1)
        assert account.balance_dollars == "$0.01"

    def test_exact_dollar(self):
        account = _make_account(balance_cents=10_000)
        assert account.balance_dollars == "$100.00"


class TestAvailableBalanceDollars:
    def test_standard_available_balance(self):
        account = _make_account(available_balance_cents=525_000)
        assert account.available_balance_dollars == "$5,250.00"

    def test_zero_available(self):
        account = _make_account(available_balance_cents=0)
        assert account.available_balance_dollars == "$0.00"

    def test_less_than_total(self):
        account = _make_account(balance_cents=50_000, available_balance_cents=20_000)
        assert account.available_balance_dollars == "$200.00"


class TestMaskedAccountNumber:
    def test_standard_account_number(self):
        account = _make_account(account_number="1000-0001-0001")
        # Uses X-based masking (different from formatting utility)
        result = account.masked_account_number
        assert result.endswith("0001")
        assert "X" in result

    def test_short_account_number_unchanged(self):
        account = _make_account(account_number="1234")
        assert account.masked_account_number == "1234"

    def test_three_char_account_unchanged(self):
        account = _make_account(account_number="ABC")
        assert account.masked_account_number == "ABC"

    def test_five_char_account(self):
        account = _make_account(account_number="12345")
        assert account.masked_account_number == "X2345"

    def test_eight_char_plain_digits(self):
        account = _make_account(account_number="12345678")
        assert account.masked_account_number == "XXXX5678"


class TestIsActive:
    def test_active_status(self):
        account = _make_account(status=AccountStatus.ACTIVE)
        assert account.is_active is True

    def test_frozen_status(self):
        account = _make_account(status=AccountStatus.FROZEN)
        assert account.is_active is False

    def test_closed_status(self):
        account = _make_account(status=AccountStatus.CLOSED)
        assert account.is_active is False
