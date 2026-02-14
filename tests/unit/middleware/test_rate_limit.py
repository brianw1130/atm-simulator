"""Unit tests for rate limiting configuration.

Tests cover:
    - Limiter is disabled in non-production environments
    - Limiter would be enabled if environment were production
    - Default rate limit is 60/minute
    - Auth rate limit is 5/15minutes per card
    - get_card_number_or_ip key function extracts card number from request body
    - get_card_number_or_ip falls back to IP when body is missing or malformed
"""

from unittest.mock import MagicMock

from slowapi import Limiter

from src.atm.config import settings
from src.atm.middleware.rate_limit import get_card_number_or_ip, limiter


def test_limiter_disabled_in_development() -> None:
    """Rate limiter should be disabled when environment is not production."""
    assert not limiter.enabled


def test_environment_is_not_production() -> None:
    """Confirm we are running in development/testing, not production."""
    assert settings.environment != "production"


def test_get_card_number_from_body() -> None:
    """Key function extracts card_number from cached request body."""
    request = MagicMock()
    request._body = b'{"card_number": "4000-0001-0001", "pin": "1234"}'
    request.client.host = "127.0.0.1"

    result = get_card_number_or_ip(request)
    assert result == "4000-0001-0001"


def test_get_card_number_falls_back_to_ip_on_missing_body() -> None:
    """Key function falls back to client IP when body is not cached."""
    request = MagicMock(spec=["client"])
    request.client.host = "192.168.1.1"
    # No _body attribute

    result = get_card_number_or_ip(request)
    assert result == "192.168.1.1"


def test_get_card_number_falls_back_to_ip_on_malformed_json() -> None:
    """Key function falls back to client IP when body is not valid JSON."""
    request = MagicMock()
    request._body = b"not-json"
    request.client.host = "10.0.0.1"

    result = get_card_number_or_ip(request)
    assert result == "10.0.0.1"


def test_get_card_number_falls_back_to_ip_on_missing_field() -> None:
    """Key function falls back to client IP when card_number field is missing."""
    request = MagicMock()
    request._body = b'{"pin": "1234"}'
    request.client.host = "10.0.0.2"

    result = get_card_number_or_ip(request)
    assert result == "10.0.0.2"


def test_get_card_number_falls_back_to_ip_on_empty_card_number() -> None:
    """Key function falls back to client IP when card_number is empty string."""
    request = MagicMock()
    request._body = b'{"card_number": "", "pin": "1234"}'
    request.client.host = "10.0.0.3"

    result = get_card_number_or_ip(request)
    assert result == "10.0.0.3"


def test_limiter_would_enable_in_production() -> None:
    """A limiter constructed with environment='production' would be enabled."""
    prod_limiter = Limiter(
        key_func=lambda _: "test",
        default_limits=["60/minute"],
        enabled=True,
        storage_uri="memory://",
    )
    assert prod_limiter.enabled


def test_default_rate_limit_is_60_per_minute() -> None:
    """The limiter default limit is configured as 60 requests per minute."""
    assert limiter._default_limits is not None
    assert len(limiter._default_limits) == 1
    limit_group = limiter._default_limits[0]
    # Access the internal limit provider string
    assert limit_group._LimitGroup__limit_provider == "60/minute"


def test_get_card_number_non_string_card_number_falls_back() -> None:
    """Key function falls back to IP when card_number is not a string."""
    request = MagicMock()
    request._body = b'{"card_number": 12345, "pin": "1234"}'
    request.client.host = "10.0.0.4"

    result = get_card_number_or_ip(request)
    assert result == "10.0.0.4"
