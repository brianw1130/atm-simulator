"""Unit tests for ATMCard model properties.

Coverage requirement: 100%

Tests: is_locked property under various locked_until values.
"""

from datetime import datetime, timedelta, timezone

import pytest

from src.atm.models.card import ATMCard


def _make_card(*, locked_until: datetime | None = None) -> ATMCard:
    """Create an ATMCard instance for property testing (no DB required)."""
    return ATMCard(
        account_id=1,
        card_number="4000-0000-0001",
        pin_hash="$2b$12$fakehashfortesting000000000000000000000000000",
        failed_attempts=0,
        locked_until=locked_until,
        is_active=True,
    )


class TestIsLocked:
    def test_not_locked_when_locked_until_is_none(self):
        card = _make_card(locked_until=None)
        assert card.is_locked is False

    def test_locked_when_locked_until_is_in_future(self):
        future = datetime.now(tz=timezone.utc) + timedelta(minutes=30)
        card = _make_card(locked_until=future)
        assert card.is_locked is True

    def test_not_locked_when_locked_until_is_in_past(self):
        past = datetime.now(tz=timezone.utc) - timedelta(minutes=30)
        card = _make_card(locked_until=past)
        assert card.is_locked is False

    def test_locked_just_one_second_in_future(self):
        future = datetime.now(tz=timezone.utc) + timedelta(seconds=1)
        card = _make_card(locked_until=future)
        assert card.is_locked is True

    def test_not_locked_just_one_second_in_past(self):
        past = datetime.now(tz=timezone.utc) - timedelta(seconds=1)
        card = _make_card(locked_until=past)
        assert card.is_locked is False
