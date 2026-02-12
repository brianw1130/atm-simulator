"""Admin panel API endpoints and template-rendered pages."""

import pathlib
from typing import Annotated, Any

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.atm.api import get_db
from src.atm.services.admin_service import (
    AdminAuthError,
    admin_logout,
    authenticate_admin,
    disable_maintenance_mode,
    enable_maintenance_mode,
    freeze_account,
    get_all_accounts,
    get_audit_logs,
    get_maintenance_status,
    unfreeze_account,
    validate_admin_session,
)

_TEMPLATES_DIR = pathlib.Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))

router = APIRouter()

DbSession = Annotated[AsyncSession, Depends(get_db)]


class AdminLoginRequest(BaseModel):
    """Request body for admin login."""

    username: str
    password: str


async def get_admin_session(
    admin_session: str | None = Cookie(default=None),
) -> dict[str, Any]:
    """Validate admin session from cookie.

    Args:
        admin_session: Session token from the admin_session cookie.

    Returns:
        Admin session data dict.

    Raises:
        HTTPException: 401 if authentication is missing or invalid.
    """
    if admin_session is None:
        raise HTTPException(status_code=401, detail="Admin authentication required")
    data = await validate_admin_session(admin_session)
    if data is None:
        raise HTTPException(status_code=401, detail="Admin session expired")
    return data


AdminSession = Annotated[dict[str, Any], Depends(get_admin_session)]


@router.post("/api/login")
async def admin_login(body: AdminLoginRequest, db: DbSession, response: Response) -> dict[str, str]:
    """Authenticate an admin user.

    Args:
        body: Login credentials.
        db: Database session.
        response: FastAPI response for setting cookies.

    Returns:
        Success message dict.
    """
    try:
        token = await authenticate_admin(db, body.username, body.password)
    except AdminAuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    response.set_cookie(
        key="admin_session",
        value=token,
        httponly=True,
        max_age=1800,
        samesite="lax",
    )
    return {"message": "Admin login successful"}


@router.post("/api/logout")
async def admin_logout_endpoint(
    admin_session: str | None = Cookie(default=None),
) -> dict[str, str]:
    """Log out the current admin session.

    Args:
        admin_session: Session token from the admin_session cookie.

    Returns:
        Logout confirmation message dict.
    """
    if admin_session:
        await admin_logout(admin_session)
    return {"message": "Logged out"}


@router.get("/api/accounts")
async def list_accounts(db: DbSession, admin: AdminSession) -> list[dict[str, Any]]:
    """List all accounts with customer info.

    Args:
        db: Database session.
        admin: Validated admin session data.

    Returns:
        List of account dicts.
    """
    return await get_all_accounts(db)


@router.post("/api/accounts/{account_id}/freeze")
async def freeze_account_endpoint(
    account_id: int,
    db: DbSession,
    admin: AdminSession,
) -> dict[str, str]:
    """Freeze an account.

    Args:
        account_id: ID of the account to freeze.
        db: Database session.
        admin: Validated admin session data.

    Returns:
        Confirmation message dict.
    """
    try:
        return await freeze_account(db, account_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/api/accounts/{account_id}/unfreeze")
async def unfreeze_account_endpoint(
    account_id: int,
    db: DbSession,
    admin: AdminSession,
) -> dict[str, str]:
    """Unfreeze an account.

    Args:
        account_id: ID of the account to unfreeze.
        db: Database session.
        admin: Validated admin session data.

    Returns:
        Confirmation message dict.
    """
    try:
        return await unfreeze_account(db, account_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/api/audit-logs")
async def list_audit_logs(
    db: DbSession,
    admin: AdminSession,
    limit: int = 100,
    event_type: str | None = None,
) -> list[dict[str, Any]]:
    """List recent audit log entries.

    Args:
        db: Database session.
        admin: Validated admin session data.
        limit: Maximum number of entries to return.
        event_type: Optional filter by event type.

    Returns:
        List of audit log dicts.
    """
    return await get_audit_logs(db, limit=limit, event_type=event_type)


# ---------------------------------------------------------------------------
# Maintenance mode endpoints
# ---------------------------------------------------------------------------


class MaintenanceRequest(BaseModel):
    """Request body for enabling maintenance mode."""

    reason: str | None = None


@router.get("/api/maintenance/status")
async def maintenance_status(admin: AdminSession) -> dict[str, Any]:
    """Get current maintenance mode status.

    Args:
        admin: Validated admin session data.

    Returns:
        Dict with enabled flag and optional reason.
    """
    return await get_maintenance_status()


@router.post("/api/maintenance/enable")
async def maintenance_enable(
    admin: AdminSession,
    body: MaintenanceRequest | None = None,
) -> dict[str, str]:
    """Enable ATM maintenance mode.

    Args:
        admin: Validated admin session data.
        body: Optional request body with reason.

    Returns:
        Confirmation message dict.
    """
    reason = body.reason if body else None
    return await enable_maintenance_mode(reason)


@router.post("/api/maintenance/disable")
async def maintenance_disable(admin: AdminSession) -> dict[str, str]:
    """Disable ATM maintenance mode.

    Args:
        admin: Validated admin session data.

    Returns:
        Confirmation message dict.
    """
    return await disable_maintenance_mode()


# ---------------------------------------------------------------------------
# Template-rendered page routes
# ---------------------------------------------------------------------------


@router.get("/login", response_class=HTMLResponse)
async def admin_login_page(request: Request) -> Response:
    """Render the admin login page.

    Args:
        request: The incoming HTTP request.

    Returns:
        Rendered login HTML page.
    """
    return templates.TemplateResponse("admin/login.html", {"request": request})


@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard_page(
    request: Request,
    db: DbSession,
    admin_session: str | None = Cookie(default=None),
) -> Response:
    """Render the admin dashboard page.

    Args:
        request: The incoming HTTP request.
        db: Database session.
        admin_session: Session token from cookie.

    Returns:
        Rendered dashboard HTML page, or redirect to login.
    """
    if admin_session is None:
        return RedirectResponse(url="/admin/login", status_code=302)
    session_data = await validate_admin_session(admin_session)
    if session_data is None:
        return RedirectResponse(url="/admin/login", status_code=302)
    accounts = await get_all_accounts(db)
    return templates.TemplateResponse(
        "admin/dashboard.html", {"request": request, "accounts": accounts}
    )


@router.get("/audit-logs", response_class=HTMLResponse)
async def admin_audit_logs_page(
    request: Request,
    db: DbSession,
    admin_session: str | None = Cookie(default=None),
    limit: int = 100,
    event_type: str | None = None,
) -> Response:
    """Render the admin audit logs page.

    Args:
        request: The incoming HTTP request.
        db: Database session.
        admin_session: Session token from cookie.
        limit: Maximum number of log entries.
        event_type: Optional event type filter.

    Returns:
        Rendered audit logs HTML page, or redirect to login.
    """
    if admin_session is None:
        return RedirectResponse(url="/admin/login", status_code=302)
    session_data = await validate_admin_session(admin_session)
    if session_data is None:
        return RedirectResponse(url="/admin/login", status_code=302)
    logs = await get_audit_logs(db, limit=limit, event_type=event_type)
    return templates.TemplateResponse("admin/audit_logs.html", {"request": request, "logs": logs})
