"""Health and readiness check endpoints.

GET /health — Liveness probe (always returns 200)
GET /ready — Readiness probe (checks DB + Redis connectivity)
"""

import asyncio

from fastapi import APIRouter
from sqlalchemy import text

from src.atm.db.session import async_session_factory

router = APIRouter(tags=["Health"])

CHECK_TIMEOUT = 2.0  # seconds


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe. Always returns healthy.

    Returns:
        Simple health status.
    """
    return {"status": "healthy"}


@router.get("/ready")
async def ready() -> dict:
    """Readiness probe. Checks database and Redis connectivity.

    Returns:
        Readiness status with individual check results.
        Returns 200 if all checks pass, 503 if any fail.
    """
    checks: dict[str, str] = {}
    all_ok = True

    # Check database
    try:
        async with async_session_factory() as session:
            await asyncio.wait_for(
                session.execute(text("SELECT 1")),
                timeout=CHECK_TIMEOUT,
            )
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {exc}"
        all_ok = False

    # Check Redis
    try:
        from src.atm.services.redis_client import get_redis
        redis = await get_redis()
        pong = await asyncio.wait_for(redis.ping(), timeout=CHECK_TIMEOUT)
        if pong:
            checks["redis"] = "ok"
        else:
            checks["redis"] = "error: ping returned False"
            all_ok = False
    except Exception as exc:
        checks["redis"] = f"error: {exc}"
        all_ok = False

    status_str = "ready" if all_ok else "not_ready"
    response = {"status": status_str, "checks": checks}

    if not all_ok:
        from fastapi.responses import JSONResponse
        return JSONResponse(content=response, status_code=503)

    return response
