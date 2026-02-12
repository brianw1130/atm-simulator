"""ASGI middleware for structured request/response logging."""

import time

import structlog
from starlette.types import ASGIApp, Receive, Scope, Send

logger = structlog.stdlib.get_logger("atm.request")

SKIP_PATHS = frozenset({"/health", "/ready"})


class RequestLoggingMiddleware:
    """Log method, path, status code, and duration for every HTTP request.

    Requests to health-check paths (``/health``, ``/ready``) are silently
    passed through without logging to avoid noise.

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

        path = scope.get("path", "")
        if path in SKIP_PATHS:
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "")
        start = time.monotonic()
        status_code = 0

        async def send_with_logging(message: dict) -> None:  # type: ignore[type-arg]
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 0)
            await send(message)

        await self.app(scope, receive, send_with_logging)

        duration_ms = round((time.monotonic() - start) * 1000, 2)
        await logger.ainfo(
            "request_completed",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
        )
