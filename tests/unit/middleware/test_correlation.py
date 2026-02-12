"""Unit tests for CorrelationIdMiddleware.

Tests cover:
    - Automatic UUID generation when X-Correlation-ID header is absent
    - Passthrough of client-supplied X-Correlation-ID header
    - Correlation ID bound to structlog context during request processing
"""

import uuid

import pytest
import structlog
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_correlation_id_generated_when_absent(client: AsyncClient) -> None:
    """A request without X-Correlation-ID gets a generated UUID in the response."""
    resp = await client.get("/health")

    assert resp.status_code == 200
    assert "x-correlation-id" in resp.headers
    # Verify the generated value is a valid UUID
    uuid.UUID(resp.headers["x-correlation-id"])


@pytest.mark.asyncio
async def test_correlation_id_passthrough(client: AsyncClient) -> None:
    """A request with X-Correlation-ID passes the value through to the response."""
    custom_id = "test-correlation-123"
    resp = await client.get("/health", headers={"X-Correlation-ID": custom_id})

    assert resp.status_code == 200
    assert resp.headers["x-correlation-id"] == custom_id


@pytest.mark.asyncio
async def test_correlation_id_unique_per_request(client: AsyncClient) -> None:
    """Each request without a correlation ID gets a unique generated value."""
    resp1 = await client.get("/health")
    resp2 = await client.get("/health")

    id1 = resp1.headers["x-correlation-id"]
    id2 = resp2.headers["x-correlation-id"]
    assert id1 != id2


@pytest.mark.asyncio
async def test_contextvars_cleared_after_request(client: AsyncClient) -> None:
    """Structlog contextvars are cleared after the request completes."""
    await client.get("/health", headers={"X-Correlation-ID": "temp-id"})

    ctx = structlog.contextvars.get_contextvars()
    assert "correlation_id" not in ctx
