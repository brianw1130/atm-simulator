"""Unit tests for Customer model properties and validators.

Coverage requirement: 100%
"""

import pytest

from src.atm.models.customer import Customer


class TestCustomerFullName:
    def test_standard_name(self):
        customer = Customer(
            first_name="Alice",
            last_name="Johnson",
            date_of_birth="1990-01-15",
            email="alice@example.com",
        )
        assert customer.full_name == "Alice Johnson"

    def test_single_character_names(self):
        customer = Customer(
            first_name="A",
            last_name="B",
            date_of_birth="1990-01-15",
            email="ab@example.com",
        )
        assert customer.full_name == "A B"

    def test_hyphenated_last_name(self):
        customer = Customer(
            first_name="Jane",
            last_name="Doe-Smith",
            date_of_birth="1985-06-20",
            email="jane@example.com",
        )
        assert customer.full_name == "Jane Doe-Smith"

    def test_full_name_format_is_first_space_last(self):
        customer = Customer(
            first_name="Bob",
            last_name="Williams",
            date_of_birth="1988-03-10",
            email="bob@example.com",
        )
        parts = customer.full_name.split(" ")
        assert len(parts) == 2
        assert parts[0] == "Bob"
        assert parts[1] == "Williams"
