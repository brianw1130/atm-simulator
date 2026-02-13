"""ASGI middleware for ATM maintenance mode.

When maintenance mode is enabled (via Redis flag), all customer-facing
API requests (``/api/v1/*``) receive a 503 Service Unavailable response.
Health checks and admin routes are always allowed through.
"""

import json

from starlette.types import ASGIApp, Receive, Scope, Send

from src.atm.services.redis_client import get_redis

MAINTENANCE_KEY = "atm:maintenance_mode"
MAINTENANCE_REASON_KEY = "atm:maintenance_reason"

# Paths that are always allowed, even during maintenance.
_ALLOWED_PREFIXES = (
    "/health",
    "/ready",
    "/admin",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/assets",
    "/favicon.ico",
)


class MaintenanceMiddleware:
    """Return 503 for customer API routes when maintenance mode is active.

    Args:
        app: The ASGI application to wrap.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Process an ASGI request."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path: str = scope.get("path", "")

        # Allow non-API and admin paths through unconditionally.
        if not path.startswith("/api/v1/"):
            await self.app(scope, receive, send)
            return

        # Check maintenance flag in Redis.
        redis = await get_redis()
        enabled = await redis.get(MAINTENANCE_KEY)
        if enabled != "1":
            await self.app(scope, receive, send)
            return

        # Maintenance mode is active — return 503.
        reason = await redis.get(MAINTENANCE_REASON_KEY) or "ATM is under maintenance"
        body = json.dumps({"detail": reason}).encode()

        await send(
            {
                "type": "http.response.start",
                "status": 503,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"retry-after", b"300"),
                ],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": body,
            }
        )
