"""Rate limiting configuration using slowapi.

Rate limiting is only enabled in production. In development and testing
environments, the limiter is disabled to avoid interfering with test suites
and local development workflows.
"""

import json

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from src.atm.config import settings


def get_card_number_or_ip(request: Request) -> str:
    """Extract card_number from the request body for auth rate limiting.

    Falls back to the client IP address if the card number cannot be
    extracted (e.g. malformed JSON, missing field).

    Args:
        request: The incoming HTTP request.

    Returns:
        The card number from the body, or the client IP address.
    """
    try:
        # Starlette caches the raw body in _body after the first read.
        # FastAPI reads the body before the route handler runs, so this
        # attribute is available when slowapi invokes the key function.
        body = getattr(request, "_body", None)
        if body:
            data = json.loads(body)
            card_number = data.get("card_number")
            if isinstance(card_number, str) and card_number:
                return card_number
    except (json.JSONDecodeError, AttributeError, TypeError):
        pass  # Fall through to IP-based rate limiting when body parsing fails
    return get_remote_address(request)


# Use in-memory storage for rate limiting.
# In production with multiple workers, switch to Redis-backed storage
# by setting storage_uri to the Redis URL.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["60/minute"],
    enabled=(settings.environment == "production"),
    storage_uri="memory://",
)
