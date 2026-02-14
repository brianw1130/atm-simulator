"""Admin panel API endpoints."""

import json as json_module
from typing import Annotated, Any

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.atm.api import get_db
from src.atm.schemas.admin import (
    AccountCreateRequest,
    AccountUpdateRequest,
    CustomerCreateRequest,
    CustomerUpdateRequest,
    PinResetRequest,
)
from src.atm.services.admin_service import (
    AdminAuthError,
    activate_customer,
    admin_logout,
    admin_reset_pin,
    authenticate_admin,
    close_account,
    create_account,
    create_customer,
    deactivate_customer,
    disable_maintenance_mode,
    enable_maintenance_mode,
    export_snapshot,
    freeze_account,
    get_all_accounts,
    get_all_customers,
    get_audit_logs,
    get_customer_detail,
    get_maintenance_status,
    import_snapshot,
    unfreeze_account,
    update_account,
    update_customer,
    validate_admin_session,
)

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
# Customer CRUD endpoints
# ---------------------------------------------------------------------------


@router.get("/api/customers")
async def list_customers(db: DbSession, admin: AdminSession) -> list[dict[str, Any]]:
    """List all customers with account counts.

    Args:
        db: Database session.
        admin: Validated admin session data.

    Returns:
        List of customer dicts.
    """
    return await get_all_customers(db)


@router.get("/api/customers/{customer_id}")
async def get_customer(
    customer_id: int,
    db: DbSession,
    admin: AdminSession,
) -> dict[str, Any]:
    """Get customer detail with accounts and cards.

    Args:
        customer_id: ID of the customer.
        db: Database session.
        admin: Validated admin session data.

    Returns:
        Customer detail dict.
    """
    result = await get_customer_detail(db, customer_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return result


@router.post("/api/customers")
async def create_customer_endpoint(
    body: CustomerCreateRequest,
    db: DbSession,
    admin: AdminSession,
) -> dict[str, Any]:
    """Create a new customer.

    Args:
        body: Customer creation data.
        db: Database session.
        admin: Validated admin session data.

    Returns:
        Created customer dict.
    """
    try:
        return await create_customer(db, body.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.put("/api/customers/{customer_id}")
async def update_customer_endpoint(
    customer_id: int,
    body: CustomerUpdateRequest,
    db: DbSession,
    admin: AdminSession,
) -> dict[str, Any]:
    """Update an existing customer.

    Args:
        customer_id: ID of the customer to update.
        body: Fields to update.
        db: Database session.
        admin: Validated admin session data.

    Returns:
        Updated customer dict.
    """
    data = body.model_dump(exclude_unset=True)
    try:
        result = await update_customer(db, customer_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return result


@router.post("/api/customers/{customer_id}/deactivate")
async def deactivate_customer_endpoint(
    customer_id: int,
    db: DbSession,
    admin: AdminSession,
) -> dict[str, str]:
    """Deactivate (soft-delete) a customer.

    Args:
        customer_id: ID of the customer to deactivate.
        db: Database session.
        admin: Validated admin session data.

    Returns:
        Confirmation message dict.
    """
    result = await deactivate_customer(db, customer_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return result


@router.post("/api/customers/{customer_id}/activate")
async def activate_customer_endpoint(
    customer_id: int,
    db: DbSession,
    admin: AdminSession,
) -> dict[str, str]:
    """Reactivate a customer.

    Args:
        customer_id: ID of the customer to activate.
        db: Database session.
        admin: Validated admin session data.

    Returns:
        Confirmation message dict.
    """
    result = await activate_customer(db, customer_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return result


# ---------------------------------------------------------------------------
# Account CRUD endpoints
# ---------------------------------------------------------------------------


@router.post("/api/customers/{customer_id}/accounts")
async def create_account_endpoint(
    customer_id: int,
    body: AccountCreateRequest,
    db: DbSession,
    admin: AdminSession,
) -> dict[str, Any]:
    """Create a new account for a customer.

    Args:
        customer_id: ID of the customer.
        body: Account creation data.
        db: Database session.
        admin: Validated admin session data.

    Returns:
        Created account dict.
    """
    try:
        return await create_account(db, customer_id, body.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/api/accounts/{account_id}")
async def update_account_endpoint(
    account_id: int,
    body: AccountUpdateRequest,
    db: DbSession,
    admin: AdminSession,
) -> dict[str, Any]:
    """Update account limits.

    Args:
        account_id: ID of the account to update.
        body: Fields to update.
        db: Database session.
        admin: Validated admin session data.

    Returns:
        Updated account dict.
    """
    data = body.model_dump(exclude_unset=True)
    result = await update_account(db, account_id, data)
    if result is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return result


@router.post("/api/accounts/{account_id}/close")
async def close_account_endpoint(
    account_id: int,
    db: DbSession,
    admin: AdminSession,
) -> dict[str, str]:
    """Close an account (balance must be zero).

    Args:
        account_id: ID of the account to close.
        db: Database session.
        admin: Validated admin session data.

    Returns:
        Confirmation message dict.
    """
    try:
        result = await close_account(db, account_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return result


# ---------------------------------------------------------------------------
# PIN management endpoints
# ---------------------------------------------------------------------------


@router.post("/api/cards/{card_id}/reset-pin")
async def reset_pin_endpoint(
    card_id: int,
    body: PinResetRequest,
    db: DbSession,
    admin: AdminSession,
) -> dict[str, str]:
    """Admin PIN reset for an ATM card.

    Args:
        card_id: ID of the ATM card.
        body: New PIN data.
        db: Database session.
        admin: Validated admin session data.

    Returns:
        Confirmation message dict.
    """
    try:
        result = await admin_reset_pin(db, card_id, body.new_pin)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="Card not found")
    return result


# ---------------------------------------------------------------------------
# Data Export / Import endpoints
# ---------------------------------------------------------------------------


@router.get("/api/export")
async def export_data(db: DbSession, admin: AdminSession) -> Response:
    """Export a complete database snapshot as a JSON file download.

    Args:
        db: Database session.
        admin: Validated admin session data.

    Returns:
        JSON response with Content-Disposition attachment header.
    """
    snapshot = await export_snapshot(db)
    content = json_module.dumps(snapshot, indent=2)
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=atm-snapshot.json"},
    )


@router.post("/api/import")
async def import_data(
    file: UploadFile,
    db: DbSession,
    admin: AdminSession,
    conflict_strategy: str = "skip",
) -> dict[str, Any]:
    """Import a JSON snapshot file into the database.

    Args:
        file: Uploaded JSON snapshot file.
        db: Database session.
        admin: Validated admin session data.
        conflict_strategy: "skip" to keep existing records, "replace" to overwrite.

    Returns:
        Summary dict with counts of imported/skipped entities.
    """
    if conflict_strategy not in ("skip", "replace"):
        raise HTTPException(status_code=422, detail="conflict_strategy must be 'skip' or 'replace'")

    try:
        raw = await file.read()
        snapshot = json_module.loads(raw)
    except (json_module.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=422, detail=f"Invalid JSON: {exc}") from exc

    try:
        stats = await import_snapshot(db, snapshot, conflict_strategy)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return stats
