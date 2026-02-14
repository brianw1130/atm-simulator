"""Unit tests for maintenance mode middleware and service functions."""

from src.atm.services.admin_service import (
    disable_maintenance_mode,
    enable_maintenance_mode,
    get_maintenance_status,
)
from src.atm.services.redis_client import get_redis

# ── Maintenance service functions ────────────────────────────────────────────


class TestEnableMaintenanceMode:
    async def test_enable_sets_redis_flag(self):
        result = await enable_maintenance_mode()
        assert result["message"] == "Maintenance mode enabled"
        redis = await get_redis()
        assert await redis.get("atm:maintenance_mode") == "1"

    async def test_enable_with_reason(self):
        await enable_maintenance_mode(reason="Scheduled upgrade")
        redis = await get_redis()
        assert await redis.get("atm:maintenance_reason") == "Scheduled upgrade"

    async def test_enable_without_reason_clears_old_reason(self):
        redis = await get_redis()
        await redis.set("atm:maintenance_reason", "old reason")
        await enable_maintenance_mode()
        assert await redis.get("atm:maintenance_reason") is None


class TestDisableMaintenanceMode:
    async def test_disable_clears_redis_flag(self):
        redis = await get_redis()
        await redis.set("atm:maintenance_mode", "1")
        result = await disable_maintenance_mode()
        assert result["message"] == "Maintenance mode disabled"
        assert await redis.get("atm:maintenance_mode") is None

    async def test_disable_clears_reason(self):
        redis = await get_redis()
        await redis.set("atm:maintenance_mode", "1")
        await redis.set("atm:maintenance_reason", "test reason")
        await disable_maintenance_mode()
        assert await redis.get("atm:maintenance_reason") is None

    async def test_disable_when_already_disabled(self):
        result = await disable_maintenance_mode()
        assert result["message"] == "Maintenance mode disabled"


class TestGetMaintenanceStatus:
    async def test_status_when_disabled(self):
        status = await get_maintenance_status()
        assert status["enabled"] is False
        assert status["reason"] is None

    async def test_status_when_enabled_with_reason(self):
        await enable_maintenance_mode(reason="Testing")
        status = await get_maintenance_status()
        assert status["enabled"] is True
        assert status["reason"] == "Testing"

    async def test_status_when_enabled_without_reason(self):
        await enable_maintenance_mode()
        status = await get_maintenance_status()
        assert status["enabled"] is True
        assert status["reason"] is None


# ── Middleware integration via test client ────────────────────────────────────


class TestMaintenanceMiddleware:
    async def test_api_returns_503_when_maintenance_enabled(self, client):
        redis = await get_redis()
        await redis.set("atm:maintenance_mode", "1")

        response = await client.get("/api/v1/auth/login")
        assert response.status_code == 503
        data = response.json()
        assert "maintenance" in data["detail"].lower()

    async def test_api_returns_503_with_custom_reason(self, client):
        redis = await get_redis()
        await redis.set("atm:maintenance_mode", "1")
        await redis.set("atm:maintenance_reason", "Cash refill in progress")

        response = await client.get("/api/v1/auth/login")
        assert response.status_code == 503
        assert response.json()["detail"] == "Cash refill in progress"

    async def test_api_passes_through_when_maintenance_disabled(self, client):
        # With maintenance disabled, we should NOT get 503.
        # We'll get some other status (e.g. 405 for GET on a POST endpoint).
        response = await client.get("/api/v1/auth/login")
        assert response.status_code != 503

    async def test_health_endpoint_passes_during_maintenance(self, client):
        redis = await get_redis()
        await redis.set("atm:maintenance_mode", "1")

        response = await client.get("/health")
        assert response.status_code == 200

    async def test_admin_endpoint_passes_during_maintenance(self, client):
        redis = await get_redis()
        await redis.set("atm:maintenance_mode", "1")

        # Admin paths must NOT be blocked by maintenance middleware.
        # The actual status depends on whether admin/dist/ is built (200 vs 404),
        # but it must never be 503.
        response = await client.get("/admin/login")
        assert response.status_code != 503

    async def test_503_includes_retry_after_header(self, client):
        redis = await get_redis()
        await redis.set("atm:maintenance_mode", "1")

        response = await client.post("/api/v1/auth/login", json={"card_number": "x", "pin": "1234"})
        assert response.status_code == 503
        assert response.headers.get("retry-after") == "300"
