"""FastAPI application factory and startup configuration."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.atm.config import settings
from src.atm.logging import configure_logging
from src.atm.middleware.correlation import CorrelationIdMiddleware
from src.atm.middleware.maintenance import MaintenanceMiddleware
from src.atm.middleware.rate_limit import limiter
from src.atm.middleware.request_logging import RequestLoggingMiddleware
from src.atm.services.redis_client import close_redis


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup and shutdown events."""
    # Startup — Redis is lazy-initialized on first use via get_redis()
    yield
    # Shutdown
    await close_redis()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    configure_logging()

    app = FastAPI(
        title="ATM Simulator",
        description="A full-featured ATM simulator with real-world banking functionality",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
    )

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

    # Middleware order matters: outermost first.
    # CorrelationId runs first (outermost), then RequestLogging, then Maintenance.
    app.add_middleware(MaintenanceMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(CorrelationIdMiddleware)

    _register_routers(app)

    return app


def _register_routers(app: FastAPI) -> None:
    """Register API route handlers.

    Args:
        app: The FastAPI application instance.
    """
    from src.atm.api.accounts import router as accounts_router
    from src.atm.api.auth import router as auth_router
    from src.atm.api.health import router as health_router
    from src.atm.api.statements import router as statements_router
    from src.atm.api.transactions import router as transactions_router

    app.include_router(health_router)
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(accounts_router, prefix="/api/v1/accounts", tags=["Accounts"])
    app.include_router(transactions_router, prefix="/api/v1/transactions", tags=["Transactions"])
    app.include_router(statements_router, prefix="/api/v1/statements", tags=["Statements"])

    from src.atm.api.admin import router as admin_router

    app.include_router(admin_router, prefix="/admin", tags=["Admin"])


app = create_app()
