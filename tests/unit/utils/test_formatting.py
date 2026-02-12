"""Unit tests for formatting utilities.

Coverage requirement: 100%

Tests mask_account_number from src/atm/utils/formatting.py.
"""

from src.atm.utils.formatting import mask_account_number


class TestMaskAccountNumber:
    def test_standard_account_with_hyphens(self):
        assert mask_account_number("1000-0001-0001") == "****-****-0001"

    def test_plain_digits_eight_chars(self):
        assert mask_account_number("12345678") == "****5678"

    def test_short_string_four_non_hyphen_chars_unchanged(self):
        assert mask_account_number("ABCD") == "ABCD"

    def test_short_string_three_chars_unchanged(self):
        assert mask_account_number("ABC") == "ABC"

    def test_short_string_two_chars_unchanged(self):
        assert mask_account_number("AB") == "AB"

    def test_single_char_unchanged(self):
        assert mask_account_number("X") == "X"

    def test_empty_string_returns_empty(self):
        assert mask_account_number("") == ""

    def test_five_non_hyphen_chars(self):
        assert mask_account_number("12345") == "*2345"

    def test_hyphens_only_four_chars(self):
        assert mask_account_number("1-2-3-4") == "1-2-3-4"

    def test_four_chars_with_hyphen(self):
        assert mask_account_number("12-34") == "12-34"

    def test_second_seed_account(self):
        assert mask_account_number("1000-0001-0002") == "****-****-0002"

    def test_six_digit_account(self):
        assert mask_account_number("123456") == "**3456"

    def test_hyphens_preserved_in_masked_output(self):
        result = mask_account_number("1000-0001-0001")
        assert result.count("-") == 2
