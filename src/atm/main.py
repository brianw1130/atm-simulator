"""FastAPI application factory and startup configuration."""

import logging
import pathlib
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.atm.config import settings
from src.atm.logging import configure_logging
from src.atm.middleware.correlation import CorrelationIdMiddleware
from src.atm.middleware.maintenance import MaintenanceMiddleware
from src.atm.middleware.rate_limit import limiter
from src.atm.middleware.request_logging import RequestLoggingMiddleware
from src.atm.services.redis_client import close_redis

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup and shutdown events."""
    # Startup — seed database with admin user and sample data (idempotent)
    from src.atm.db.seed import seed_database
    from src.atm.db.session import async_session_factory

    async with async_session_factory() as session:
        try:
            await seed_database(session)
            await session.commit()
            logger.info("Database seeding completed successfully.")
        except Exception:
            await session.rollback()
            logger.exception("Database seeding failed.")

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

    # CORS — allow Vite dev server in development mode.
    if settings.is_development:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:5173", "http://localhost:5174"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Middleware order matters: outermost first.
    # CorrelationId runs first (outermost), then RequestLogging, then Maintenance.
    app.add_middleware(MaintenanceMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(CorrelationIdMiddleware)

    _register_routers(app)
    _mount_admin_frontend(app)
    _mount_frontend(app)

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


def _mount_admin_frontend(app: FastAPI) -> None:
    """Mount the admin React SPA static files and catch-all route.

    In production, the admin build output lives at ``admin/dist/``.
    If the directory does not exist (e.g. in tests or when ``frontend_enabled``
    is ``False``), this function is a no-op.

    Must be called after ``_register_routers()`` so that ``/admin/api/*`` routes
    take priority over the SPA catch-all.

    Args:
        app: The FastAPI application instance.
    """
    if not settings.frontend_enabled:
        return  # pragma: no cover

    admin_dir = pathlib.Path(__file__).resolve().parent.parent.parent / "admin" / "dist"
    if not admin_dir.exists():
        return

    admin_assets = admin_dir / "assets"
    if admin_assets.exists():
        app.mount(
            "/admin/assets",
            StaticFiles(directory=str(admin_assets)),
            name="admin-static-assets",
        )

    admin_index = admin_dir / "index.html"

    @app.get("/admin/{path:path}", response_class=FileResponse, include_in_schema=False)
    async def serve_admin_spa(path: str) -> FileResponse:
        """Serve admin SPA — static files or fall back to index.html."""
        file_path = admin_dir / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(admin_index))


def _mount_frontend(app: FastAPI) -> None:
    """Mount the React SPA static files and catch-all route.

    In production, the React build output lives at ``frontend/dist/``.
    If the directory does not exist (e.g. in tests or when ``frontend_enabled``
    is ``False``), this function is a no-op.

    Args:
        app: The FastAPI application instance.
    """
    if not settings.frontend_enabled:
        return

    frontend_dir = pathlib.Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
    if not frontend_dir.exists():
        return

    assets_dir = frontend_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="static-assets")

    index_html = frontend_dir / "index.html"

    @app.get("/", response_class=FileResponse, include_in_schema=False)
    async def serve_spa_root() -> FileResponse:
        """Serve the React SPA index page."""
        return FileResponse(str(index_html))

    @app.get("/{path:path}", response_class=FileResponse, include_in_schema=False)
    async def serve_spa_fallback(path: str) -> FileResponse:
        """Serve static files or fall back to index.html for client-side routing."""
        file_path = frontend_dir / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(index_html))


app = create_app()
