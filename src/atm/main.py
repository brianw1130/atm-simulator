"""FastAPI application factory and startup configuration."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from src.atm.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    # TODO: Initialize database connection pool
    # TODO: Run any startup checks
    yield
    # Shutdown
    # TODO: Close database connections gracefully


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title="ATM Simulator",
        description="A full-featured ATM simulator with real-world banking functionality",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
    )

    _register_routers(app)

    return app


def _register_routers(app: FastAPI) -> None:
    """Register API route handlers.

    Args:
        app: The FastAPI application instance.
    """
    # TODO: Import and include routers as they are implemented
    # from src.atm.api.auth import router as auth_router
    # from src.atm.api.accounts import router as accounts_router
    # from src.atm.api.transactions import router as transactions_router
    # from src.atm.api.statements import router as statements_router
    #
    # app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
    # app.include_router(accounts_router, prefix="/api/v1/accounts", tags=["Accounts"])
    # app.include_router(transactions_router, prefix="/api/v1/transactions", tags=["Transactions"])
    # app.include_router(statements_router, prefix="/api/v1/statements", tags=["Statements"])

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy"}


app = create_app()
