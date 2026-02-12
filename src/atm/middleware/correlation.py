"""ASGI middleware for correlation ID propagation."""

import uuid

import structlog
from starlette.types import ASGIApp, Receive, Scope, Send


class CorrelationIdMiddleware:
    """Attach a correlation ID to every HTTP request.

    Reads ``X-Correlation-ID`` from incoming request headers. If absent,
    generates a new UUID4. The ID is bound to the structlog context for
    the duration of the request and returned in the response headers.

    Args:
        app: The ASGI application to wrap.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Process an ASGI request."""
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        correlation_id = (
            headers.get(b"x-correlation-id", b"").decode() or str(uuid.uuid4())
        )

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

        async def send_with_correlation(message: dict) -> None:  # type: ignore[type-arg]
            if message["type"] == "http.response.start":
                resp_headers: list[tuple[bytes, bytes]] = list(
                    message.get("headers", [])
                )
                resp_headers.append(
                    (b"x-correlation-id", correlation_id.encode())
                )
                message["headers"] = resp_headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_correlation)
        finally:
            structlog.contextvars.clear_contextvars()
