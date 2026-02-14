"""Unit tests for admin CRUD Pydantic schemas.

Coverage requirement: 100%

Tests CustomerCreateRequest, CustomerUpdateRequest, AccountCreateRequest,
AccountUpdateRequest, PinResetRequest from src/atm/schemas/admin.py.
"""

from datetime import date

import pytest
from pydantic import ValidationError

from src.atm.schemas.admin import (
    AccountCreateRequest,
    AccountUpdateRequest,
    CustomerCreateRequest,
    CustomerUpdateRequest,
    PinResetRequest,
)

# ── CustomerCreateRequest ───────────────────────────────────────────────────


class TestCustomerCreateRequest:
    def test_valid_customer(self):
        req = CustomerCreateRequest(
            first_name="Alice",
            last_name="Johnson",
            date_of_birth=date(1990, 5, 15),
            email="alice@example.com",
        )
        assert req.first_name == "Alice"
        assert req.phone is None

    def test_valid_with_phone(self):
        req = CustomerCreateRequest(
            first_name="Alice",
            last_name="Johnson",
            date_of_birth=date(1990, 5, 15),
            email="alice@example.com",
            phone="555-0101",
        )
        assert req.phone == "555-0101"

    def test_missing_required_fields_rejected(self):
        with pytest.raises(ValidationError):
            CustomerCreateRequest(
                first_name="Alice",
            )  # type: ignore[call-arg]

    def test_empty_first_name_rejected(self):
        with pytest.raises(ValidationError):
            CustomerCreateRequest(
                first_name="",
                last_name="Johnson",
                date_of_birth=date(1990, 5, 15),
                email="alice@example.com",
            )

    def test_invalid_email_rejected(self):
        with pytest.raises(ValidationError):
            CustomerCreateRequest(
                first_name="Alice",
                last_name="Johnson",
                date_of_birth=date(1990, 5, 15),
                email="not-an-email",
            )

    def test_name_too_long_rejected(self):
        with pytest.raises(ValidationError):
            CustomerCreateRequest(
                first_name="A" * 101,
                last_name="Johnson",
                date_of_birth=date(1990, 5, 15),
                email="alice@example.com",
            )


# ── CustomerUpdateRequest ──────────────────────────────────────────────────


class TestCustomerUpdateRequest:
    def test_all_none_is_valid(self):
        req = CustomerUpdateRequest()
        assert req.first_name is None
        assert req.email is None

    def test_partial_update(self):
        req = CustomerUpdateRequest(first_name="Bob")
        assert req.first_name == "Bob"
        assert req.last_name is None

    def test_invalid_email_rejected(self):
        with pytest.raises(ValidationError):
            CustomerUpdateRequest(email="bad-email")


# ── AccountCreateRequest ───────────────────────────────────────────────────


class TestAccountCreateRequest:
    def test_valid_checking(self):
        req = AccountCreateRequest(account_type="CHECKING")
        assert req.account_type == "CHECKING"
        assert req.initial_balance_cents == 0

    def test_valid_savings_with_balance(self):
        req = AccountCreateRequest(
            account_type="SAVINGS",
            initial_balance_cents=100000,
        )
        assert req.initial_balance_cents == 100000

    def test_invalid_type_rejected(self):
        with pytest.raises(ValidationError):
            AccountCreateRequest(account_type="INVALID")

    def test_negative_balance_rejected(self):
        with pytest.raises(ValidationError):
            AccountCreateRequest(account_type="CHECKING", initial_balance_cents=-100)


# ── AccountUpdateRequest ──────────────────────────────────────────────────


class TestAccountUpdateRequest:
    def test_empty_update_valid(self):
        req = AccountUpdateRequest()
        assert req.daily_withdrawal_limit_cents is None
        assert req.daily_transfer_limit_cents is None

    def test_valid_limits(self):
        req = AccountUpdateRequest(
            daily_withdrawal_limit_cents=100000,
            daily_transfer_limit_cents=500000,
        )
        assert req.daily_withdrawal_limit_cents == 100000

    def test_zero_limit_rejected(self):
        with pytest.raises(ValidationError):
            AccountUpdateRequest(daily_withdrawal_limit_cents=0)


# ── PinResetRequest ────────────────────────────────────────────────────────


class TestPinResetRequest:
    def test_valid_pin(self):
        req = PinResetRequest(new_pin="4829")
        assert req.new_pin == "4829"

    def test_valid_six_digit_pin(self):
        req = PinResetRequest(new_pin="482937")
        assert req.new_pin == "482937"

    def test_non_digit_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            PinResetRequest(new_pin="ab12")
        assert "digits" in str(exc_info.value)

    def test_all_same_digit_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            PinResetRequest(new_pin="1111")
        assert "same digit" in str(exc_info.value)

    def test_sequential_ascending_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            PinResetRequest(new_pin="1234")
        assert "sequential" in str(exc_info.value).lower()

    def test_sequential_descending_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            PinResetRequest(new_pin="4321")
        assert "sequential" in str(exc_info.value).lower()

    def test_too_short_rejected(self):
        with pytest.raises(ValidationError):
            PinResetRequest(new_pin="12")

    def test_too_long_rejected(self):
        with pytest.raises(ValidationError):
            PinResetRequest(new_pin="1234567")
