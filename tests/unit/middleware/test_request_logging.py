"""Unit tests for RequestLoggingMiddleware.

Tests cover:
    - Health and readiness paths are excluded from request logging
    - Non-health paths produce log output
"""

import logging

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_path_not_logged(
    client: AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    """Requests to /health are not logged by the request logging middleware."""
    with caplog.at_level(logging.INFO, logger="atm.request"):
        await client.get("/health")

    assert not any("request_completed" in r.message for r in caplog.records)


@pytest.mark.asyncio
async def test_ready_path_not_logged(client: AsyncClient, caplog: pytest.LogCaptureFixture) -> None:
    """Requests to /ready are not logged by the request logging middleware."""
    with caplog.at_level(logging.INFO, logger="atm.request"):
        await client.get("/ready")

    assert not any("request_completed" in r.message for r in caplog.records)


@pytest.mark.asyncio
async def test_non_health_path_is_logged(
    client: AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    """Requests to non-health paths produce a request_completed log entry."""
    with caplog.at_level(logging.INFO, logger="atm.request"):
        await client.post(
            "/api/v1/auth/login",
            json={"card_number": "9999-9999-9999", "pin": "0000"},
        )

    assert any("request_completed" in r.message for r in caplog.records)
