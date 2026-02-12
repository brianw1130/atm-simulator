"""Redis client management for the ATM simulator.

Provides async Redis connection with support for test injection (fakeredis).
"""

import redis.asyncio as aioredis

from src.atm.config import settings

_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Get the Redis client instance.

    Returns:
        The async Redis client.

    Raises:
        RuntimeError: If Redis has not been initialized.
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(  # type: ignore[no-untyped-call]
            settings.redis_url,
            decode_responses=True,
        )
    return _redis_client


def set_redis(client: aioredis.Redis) -> None:
    """Override the Redis client (for testing with fakeredis).

    Args:
        client: A Redis-compatible client instance.
    """
    global _redis_client
    _redis_client = client


async def close_redis() -> None:
    """Close the Redis connection gracefully."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
