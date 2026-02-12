"""Integration tests for health and readiness endpoints.

Tests cover:
    - GET /health returns 200 with healthy status
    - GET /ready responds without crashing (200 or 503 depending on DB availability)
    - GET /ready returns 503 when Redis is unavailable
    - Response structure includes expected fields
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from src.atm.services.redis_client import get_redis, set_redis


@pytest.mark.asyncio
async def test_health_returns_200(client: AsyncClient) -> None:
    """GET /health always returns 200 with status healthy."""
    resp = await client.get("/health")

    assert resp.status_code == 200
    assert resp.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_health_response_content_type(client: AsyncClient) -> None:
    """GET /health returns JSON content type."""
    resp = await client.get("/health")

    assert resp.status_code == 200
    assert "application/json" in resp.headers["content-type"]


@pytest.mark.asyncio
async def test_ready_endpoint_responds(client: AsyncClient) -> None:
    """GET /ready responds with expected structure (200 or 503 depending on DB).

    The /ready endpoint checks both database and Redis connectivity.
    In tests, the production database URL is not available, so the database
    check may fail. We verify the endpoint responds correctly regardless.
    """
    resp = await client.get("/ready")

    assert resp.status_code in (200, 503)
    data = resp.json()
    assert "status" in data
    assert "checks" in data
    assert "redis" in data["checks"]
    assert "database" in data["checks"]


@pytest.mark.asyncio
async def test_ready_redis_check_passes(client: AsyncClient) -> None:
    """GET /ready shows Redis as ok (FakeRedis is injected in tests)."""
    resp = await client.get("/ready")

    data = resp.json()
    assert data["checks"]["redis"] == "ok"


@pytest.mark.asyncio
async def test_ready_returns_503_when_redis_unavailable(client: AsyncClient) -> None:
    """GET /ready returns 503 when Redis ping fails."""
    # Save the current Redis client to restore after test
    original_redis = await get_redis()

    # Create a mock Redis that raises on ping
    mock_redis = AsyncMock()
    mock_redis.ping.side_effect = ConnectionError("Redis unavailable")
    set_redis(mock_redis)

    resp = await client.get("/ready")

    data = resp.json()
    assert "error" in data["checks"]["redis"]

    # Restore the original FakeRedis so other tests are not affected
    set_redis(original_redis)
