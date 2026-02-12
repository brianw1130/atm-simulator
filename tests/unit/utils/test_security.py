"""Unit tests for security utilities.

Coverage requirement: 100%

Tests all functions in src/atm/utils/security.py:
    - hash_pin
    - verify_pin
    - generate_session_token
    - generate_reference_number
    - validate_pin_complexity
    - sanitize_input
"""

import pytest

from src.atm.utils.security import (
    generate_reference_number,
    generate_session_token,
    hash_pin,
    sanitize_input,
    validate_pin_complexity,
    verify_pin,
)

PEPPER = "test-pepper-value"


# ── hash_pin ─────────────────────────────────────────────────────────────────


class TestHashPin:
    def test_valid_pin_produces_bcrypt_hash(self):
        result = hash_pin("1234", PEPPER)
        assert isinstance(result, str)
        assert result.startswith("$2")

    def test_different_pins_produce_different_hashes(self):
        hash1 = hash_pin("1234", PEPPER)
        hash2 = hash_pin("5678", PEPPER)
        assert hash1 != hash2

    def test_same_pin_produces_different_hashes_due_to_salt(self):
        hash1 = hash_pin("1234", PEPPER)
        hash2 = hash_pin("1234", PEPPER)
        assert hash1 != hash2

    def test_empty_pin_raises_value_error(self):
        with pytest.raises(ValueError, match="PIN must not be empty"):
            hash_pin("", PEPPER)

    def test_empty_pepper_raises_value_error(self):
        with pytest.raises(ValueError, match="Pepper must not be empty"):
            hash_pin("1234", "")


# ── verify_pin ───────────────────────────────────────────────────────────────


class TestVerifyPin:
    def test_correct_pin_returns_true(self):
        pin_hash = hash_pin("5678", PEPPER)
        assert verify_pin("5678", pin_hash, PEPPER) is True

    def test_wrong_pin_returns_false(self):
        pin_hash = hash_pin("5678", PEPPER)
        assert verify_pin("9999", pin_hash, PEPPER) is False

    def test_wrong_pepper_returns_false(self):
        pin_hash = hash_pin("5678", PEPPER)
        assert verify_pin("5678", pin_hash, "wrong-pepper") is False

    def test_empty_pin_returns_false(self):
        pin_hash = hash_pin("5678", PEPPER)
        assert verify_pin("", pin_hash, PEPPER) is False

    def test_empty_hash_returns_false(self):
        assert verify_pin("5678", "", PEPPER) is False

    def test_empty_pepper_returns_false(self):
        pin_hash = hash_pin("5678", PEPPER)
        assert verify_pin("5678", pin_hash, "") is False

    def test_malformed_hash_returns_false(self):
        assert verify_pin("5678", "not-a-bcrypt-hash", PEPPER) is False

    def test_none_like_empty_inputs_return_false(self):
        assert verify_pin("", "", "") is False


# ── generate_session_token ───────────────────────────────────────────────────


class TestGenerateSessionToken:
    def test_returns_string(self):
        token = generate_session_token()
        assert isinstance(token, str)

    def test_token_length_is_approximately_43(self):
        token = generate_session_token()
        assert len(token) == 43

    def test_two_tokens_are_different(self):
        token1 = generate_session_token()
        token2 = generate_session_token()
        assert token1 != token2

    def test_token_is_url_safe(self):
        token = generate_session_token()
        allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")
        assert all(c in allowed for c in token)


# ── generate_reference_number ────────────────────────────────────────────────


class TestGenerateReferenceNumber:
    def test_starts_with_ref_prefix(self):
        ref = generate_reference_number()
        assert ref.startswith("REF-")

    def test_contains_hyphens(self):
        ref = generate_reference_number()
        parts = ref.split("-")
        assert len(parts) == 3

    def test_two_calls_produce_different_refs(self):
        ref1 = generate_reference_number()
        ref2 = generate_reference_number()
        assert ref1 != ref2

    def test_format_structure(self):
        ref = generate_reference_number()
        prefix, timestamp_hex, random_hex = ref.split("-")
        assert prefix == "REF"
        # timestamp_hex should be valid hex
        int(timestamp_hex, 16)
        # random_hex should be 8 hex chars (4 bytes)
        assert len(random_hex) == 8
        int(random_hex, 16)


# ── validate_pin_complexity ──────────────────────────────────────────────────


class TestValidatePinComplexity:
    @pytest.mark.parametrize("pin", ["7856", "48293", "192837", "3917", "80264"])
    def test_valid_pins_accepted(self, pin):
        is_valid, reason = validate_pin_complexity(pin)
        assert is_valid is True
        assert reason == ""

    @pytest.mark.parametrize("pin", ["1111", "0000", "000000", "2222", "999999"])
    def test_all_same_digit_rejected(self, pin):
        is_valid, reason = validate_pin_complexity(pin)
        assert is_valid is False
        assert "same digit" in reason

    @pytest.mark.parametrize("pin", ["1234", "12345", "123456", "0123"])
    def test_sequential_ascending_rejected(self, pin):
        is_valid, _reason = validate_pin_complexity(pin)
        assert is_valid is False

    @pytest.mark.parametrize("pin", ["4321", "54321", "654321"])
    def test_sequential_descending_rejected(self, pin):
        is_valid, _reason = validate_pin_complexity(pin)
        assert is_valid is False

    @pytest.mark.parametrize("pin", ["0000", "9876", "1357", "2468"])
    def test_common_pins_rejected(self, pin):
        is_valid, _reason = validate_pin_complexity(pin)
        assert is_valid is False

    def test_non_digit_characters_rejected(self):
        is_valid, reason = validate_pin_complexity("12ab")
        assert is_valid is False
        assert "digits" in reason

    def test_letters_only_rejected(self):
        is_valid, reason = validate_pin_complexity("abcd")
        assert is_valid is False
        assert "digits" in reason

    def test_too_short_rejected(self):
        is_valid, reason = validate_pin_complexity("12")
        assert is_valid is False
        assert "4-6 digits" in reason

    def test_three_digits_rejected(self):
        is_valid, _reason = validate_pin_complexity("123")
        assert is_valid is False

    def test_too_long_rejected(self):
        is_valid, reason = validate_pin_complexity("1234567")
        assert is_valid is False
        assert "4-6 digits" in reason

    def test_empty_string_rejected(self):
        is_valid, reason = validate_pin_complexity("")
        assert is_valid is False
        assert "digits" in reason

    def test_special_characters_rejected(self):
        is_valid, _reason = validate_pin_complexity("12!4")
        assert is_valid is False


# ── sanitize_input ───────────────────────────────────────────────────────────


class TestSanitizeInput:
    def test_strips_leading_whitespace(self):
        assert sanitize_input("  hello") == "hello"

    def test_strips_trailing_whitespace(self):
        assert sanitize_input("hello  ") == "hello"

    def test_strips_both_whitespace(self):
        assert sanitize_input("  hello  ") == "hello"

    def test_removes_null_bytes(self):
        assert sanitize_input("hel\x00lo") == "hello"

    def test_escapes_less_than(self):
        result = sanitize_input("<script>")
        assert "<" not in result
        assert "&lt;" in result

    def test_escapes_greater_than(self):
        result = sanitize_input("a>b")
        assert ">" not in result
        assert "&gt;" in result

    def test_escapes_ampersand(self):
        result = sanitize_input("a&b")
        assert result == "a&amp;b"

    def test_escapes_double_quote(self):
        result = sanitize_input('a"b')
        assert '"' not in result
        assert "&quot;" in result

    def test_escapes_single_quote(self):
        result = sanitize_input("a'b")
        assert "'" not in result
        assert "&#x27;" in result

    def test_combined_sanitization(self):
        result = sanitize_input("  \x00<script>alert('xss')  ")
        assert "\x00" not in result
        assert "<" not in result
        assert "'" not in result
        assert result.startswith("&lt;")

    def test_clean_input_unchanged(self):
        assert sanitize_input("hello world") == "hello world"

    def test_empty_string(self):
        assert sanitize_input("") == ""
