"""Unit tests for authentication Pydantic schemas.

Coverage requirement: 100%

Tests LoginRequest, LoginResponse, PinChangeRequest, PinChangeResponse
from src/atm/schemas/auth.py.
"""

import pytest
from pydantic import ValidationError

from src.atm.schemas.auth import (
    LoginRequest,
    LoginResponse,
    PinChangeRequest,
    PinChangeResponse,
)


# ── LoginRequest ─────────────────────────────────────────────────────────────


class TestLoginRequest:
    def test_valid_login(self):
        req = LoginRequest(card_number="1000-0001-0001", pin="1234")
        assert req.card_number == "1000-0001-0001"
        assert req.pin == "1234"

    def test_valid_six_digit_pin(self):
        req = LoginRequest(card_number="1000-0001-0001", pin="123456")
        assert req.pin == "123456"

    def test_non_digit_pin_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            LoginRequest(card_number="1000-0001-0001", pin="12ab")
        assert "PIN must contain only digits" in str(exc_info.value)

    def test_pin_too_short_rejected(self):
        with pytest.raises(ValidationError):
            LoginRequest(card_number="1000-0001-0001", pin="123")

    def test_pin_too_long_rejected(self):
        with pytest.raises(ValidationError):
            LoginRequest(card_number="1000-0001-0001", pin="1234567")

    def test_empty_card_number_rejected(self):
        with pytest.raises(ValidationError):
            LoginRequest(card_number="", pin="1234")

    def test_card_number_too_long_rejected(self):
        with pytest.raises(ValidationError):
            LoginRequest(card_number="A" * 21, pin="1234")

    def test_missing_card_number_rejected(self):
        with pytest.raises(ValidationError):
            LoginRequest(pin="1234")  # type: ignore[call-arg]

    def test_missing_pin_rejected(self):
        with pytest.raises(ValidationError):
            LoginRequest(card_number="1000-0001-0001")  # type: ignore[call-arg]


# ── LoginResponse ────────────────────────────────────────────────────────────


class TestLoginResponse:
    def test_valid_response(self):
        resp = LoginResponse(
            session_id="abc123",
            account_number="****-****-0001",
            customer_name="Alice Johnson",
        )
        assert resp.session_id == "abc123"
        assert resp.message == "Authentication successful"

    def test_custom_message(self):
        resp = LoginResponse(
            session_id="abc123",
            account_number="****-****-0001",
            customer_name="Alice",
            message="Welcome back",
        )
        assert resp.message == "Welcome back"


# ── PinChangeRequest ─────────────────────────────────────────────────────────


class TestPinChangeRequest:
    def test_valid_pin_change(self):
        req = PinChangeRequest(
            current_pin="7856",
            new_pin="4829",
            confirm_pin="4829",
        )
        assert req.new_pin == "4829"

    def test_valid_six_digit_pin_change(self):
        req = PinChangeRequest(
            current_pin="785612",
            new_pin="482937",
            confirm_pin="482937",
        )
        assert req.new_pin == "482937"

    def test_mismatched_confirm_pin_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            PinChangeRequest(
                current_pin="7856",
                new_pin="4829",
                confirm_pin="9999",
            )
        assert "PINs do not match" in str(exc_info.value)

    def test_all_same_digit_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            PinChangeRequest(
                current_pin="7856",
                new_pin="1111",
                confirm_pin="1111",
            )
        assert "same digit" in str(exc_info.value)

    def test_sequential_ascending_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            PinChangeRequest(
                current_pin="7856",
                new_pin="1234",
                confirm_pin="1234",
            )
        assert "sequential" in str(exc_info.value).lower()

    def test_sequential_descending_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            PinChangeRequest(
                current_pin="7856",
                new_pin="4321",
                confirm_pin="4321",
            )
        assert "sequential" in str(exc_info.value).lower()

    def test_non_digit_new_pin_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            PinChangeRequest(
                current_pin="7856",
                new_pin="ab12",
                confirm_pin="ab12",
            )
        assert "digits" in str(exc_info.value)

    def test_new_pin_too_short_rejected(self):
        with pytest.raises(ValidationError):
            PinChangeRequest(
                current_pin="7856",
                new_pin="12",
                confirm_pin="12",
            )

    def test_new_pin_too_long_rejected(self):
        with pytest.raises(ValidationError):
            PinChangeRequest(
                current_pin="7856",
                new_pin="1234567",
                confirm_pin="1234567",
            )


# ── PinChangeResponse ────────────────────────────────────────────────────────


class TestPinChangeResponse:
    def test_default_message(self):
        resp = PinChangeResponse()
        assert resp.message == "PIN changed successfully"

    def test_custom_message(self):
        resp = PinChangeResponse(message="Done")
        assert resp.message == "Done"
