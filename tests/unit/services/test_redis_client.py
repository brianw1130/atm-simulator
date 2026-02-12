"""Unit tests for the Redis client management module.

Tests cover:
    - set_redis overrides the global client
    - get_redis returns the injected client
    - close_redis resets the global client
"""

import fakeredis.aioredis
import pytest

from src.atm.services.redis_client import close_redis, get_redis, set_redis


@pytest.mark.asyncio
async def test_set_redis_overrides_client() -> None:
    """set_redis injects a custom client that get_redis returns."""
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    set_redis(fake)

    client = await get_redis()
    assert client is fake


@pytest.mark.asyncio
async def test_get_redis_returns_same_instance() -> None:
    """Consecutive get_redis calls return the same client instance."""
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    set_redis(fake)

    client1 = await get_redis()
    client2 = await get_redis()
    assert client1 is client2


@pytest.mark.asyncio
async def test_close_redis_resets_client() -> None:
    """close_redis clears the global client so a new one can be injected."""
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    set_redis(fake)
    await close_redis()

    # After closing, inject a new fake to avoid connecting to real Redis
    fake2 = fakeredis.aioredis.FakeRedis(decode_responses=True)
    set_redis(fake2)

    client = await get_redis()
    assert client is fake2
    assert client is not fake
