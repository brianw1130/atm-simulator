"""Integration tests for admin API endpoints.

Tests cover: login, logout, account listing, freeze/unfreeze, audit logs,
and template-rendered pages (login, dashboard, audit logs).
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.atm.models.audit import AuditEventType, AuditLog
from src.atm.services.admin_service import create_admin_user
from tests.factories import create_test_account, create_test_customer

pytestmark = pytest.mark.asyncio

ADMIN_USER = "admin"
ADMIN_PASS = "adminpass123"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_admin(db_session: AsyncSession) -> None:
    """Create an admin user for tests."""
    await create_admin_user(db_session, ADMIN_USER, ADMIN_PASS)
    await db_session.commit()


async def _login(client: AsyncClient) -> dict:
    """Login as admin and return cookies dict."""
    resp = await client.post(
        "/admin/api/login",
        json={"username": ADMIN_USER, "password": ADMIN_PASS},
    )
    assert resp.status_code == 200
    return dict(resp.cookies)


async def _seed_account(db_session: AsyncSession) -> int:
    """Create a customer with one checking account. Returns account ID."""
    customer = await create_test_customer(db_session, first_name="Alice", last_name="Johnson")
    account = await create_test_account(
        db_session,
        customer_id=customer.id,
        account_number="1000-0001-0001",
        balance_cents=525_000,
    )
    await db_session.commit()
    return account.id


async def _seed_audit_logs(db_session: AsyncSession) -> None:
    """Create sample audit log entries."""
    db_session.add(AuditLog(event_type=AuditEventType.LOGIN_SUCCESS, details={"card": "***0001"}))
    db_session.add(AuditLog(event_type=AuditEventType.WITHDRAWAL, details={"amount": 10000}))
    db_session.add(
        AuditLog(event_type=AuditEventType.LOGIN_FAILED, details={"reason": "wrong PIN"})
    )
    await db_session.flush()
    await db_session.commit()


# ===========================================================================
# POST /admin/api/login
# ===========================================================================


class TestAdminLogin:
    async def test_valid_credentials_returns_200_and_sets_cookie(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Valid admin credentials return 200 with an admin_session cookie."""
        await _create_admin(db_session)
        resp = await client.post(
            "/admin/api/login",
            json={"username": ADMIN_USER, "password": ADMIN_PASS},
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "Admin login successful"
        assert "admin_session" in resp.cookies

    async def test_invalid_credentials_returns_401(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Invalid credentials return 401."""
        await _create_admin(db_session)
        resp = await client.post(
            "/admin/api/login",
            json={"username": ADMIN_USER, "password": "wrongpassword"},
        )
        assert resp.status_code == 401

    async def test_nonexistent_user_returns_401(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """A user that does not exist returns 401."""
        resp = await client.post(
            "/admin/api/login",
            json={"username": "nobody", "password": "anypass"},
        )
        assert resp.status_code == 401


# ===========================================================================
# POST /admin/api/logout
# ===========================================================================


class TestAdminLogout:
    async def test_logout_with_cookie(self, client: AsyncClient, db_session: AsyncSession) -> None:
        """Logout with a valid cookie returns 200."""
        await _create_admin(db_session)
        cookies = await _login(client)
        resp = await client.post("/admin/api/logout", cookies=cookies)
        assert resp.status_code == 200
        assert resp.json()["message"] == "Logged out"

    async def test_logout_without_cookie(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Logout without a cookie still returns 200 (no-op)."""
        resp = await client.post("/admin/api/logout")
        assert resp.status_code == 200
        assert resp.json()["message"] == "Logged out"


# ===========================================================================
# GET /admin/api/accounts
# ===========================================================================


class TestListAccounts:
    async def test_with_admin_session_returns_accounts(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Authenticated admin can list all accounts."""
        await _create_admin(db_session)
        await _seed_account(db_session)
        cookies = await _login(client)

        resp = await client.get("/admin/api/accounts", cookies=cookies)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["account_number"] == "1000-0001-0001"

    async def test_without_auth_returns_401(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Unauthenticated request to list accounts returns 401."""
        resp = await client.get("/admin/api/accounts")
        assert resp.status_code == 401


# ===========================================================================
# POST /admin/api/accounts/{id}/freeze
# ===========================================================================


class TestFreezeAccountEndpoint:
    async def test_freeze_with_admin_auth(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Authenticated admin can freeze an account."""
        await _create_admin(db_session)
        account_id = await _seed_account(db_session)
        cookies = await _login(client)

        resp = await client.post(f"/admin/api/accounts/{account_id}/freeze", cookies=cookies)
        assert resp.status_code == 200
        assert "frozen" in resp.json()["message"].lower()

    async def test_freeze_without_auth_returns_401(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Unauthenticated freeze attempt returns 401."""
        account_id = await _seed_account(db_session)
        resp = await client.post(f"/admin/api/accounts/{account_id}/freeze")
        assert resp.status_code == 401

    async def test_freeze_account_not_found_returns_404(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Freeze of a nonexistent account returns 404."""
        await _create_admin(db_session)
        cookies = await _login(client)

        resp = await client.post("/admin/api/accounts/99999/freeze", cookies=cookies)
        assert resp.status_code == 404


# ===========================================================================
# POST /admin/api/accounts/{id}/unfreeze
# ===========================================================================


class TestUnfreezeAccountEndpoint:
    async def test_unfreeze_with_admin_auth(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Authenticated admin can unfreeze a frozen account."""
        await _create_admin(db_session)
        account_id = await _seed_account(db_session)
        cookies = await _login(client)

        # Freeze first
        await client.post(f"/admin/api/accounts/{account_id}/freeze", cookies=cookies)
        # Unfreeze
        resp = await client.post(f"/admin/api/accounts/{account_id}/unfreeze", cookies=cookies)
        assert resp.status_code == 200
        assert "unfrozen" in resp.json()["message"].lower()

    async def test_unfreeze_without_auth_returns_401(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Unauthenticated unfreeze attempt returns 401."""
        account_id = await _seed_account(db_session)
        resp = await client.post(f"/admin/api/accounts/{account_id}/unfreeze")
        assert resp.status_code == 401

    async def test_unfreeze_account_not_found_returns_404(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Unfreeze of a nonexistent account returns 404."""
        await _create_admin(db_session)
        cookies = await _login(client)

        resp = await client.post("/admin/api/accounts/99999/unfreeze", cookies=cookies)
        assert resp.status_code == 404


# ===========================================================================
# GET /admin/api/audit-logs
# ===========================================================================


class TestListAuditLogs:
    async def test_with_admin_auth_returns_logs(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Authenticated admin can list audit logs."""
        await _create_admin(db_session)
        await _seed_audit_logs(db_session)
        cookies = await _login(client)

        resp = await client.get("/admin/api/audit-logs", cookies=cookies)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 3

    async def test_filter_by_event_type(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Audit logs can be filtered by event_type query parameter."""
        await _create_admin(db_session)
        await _seed_audit_logs(db_session)
        cookies = await _login(client)

        resp = await client.get(
            "/admin/api/audit-logs",
            params={"event_type": "LOGIN_FAILED"},
            cookies=cookies,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["event_type"] == "LOGIN_FAILED"

    async def test_without_auth_returns_401(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Unauthenticated request returns 401."""
        resp = await client.get("/admin/api/audit-logs")
        assert resp.status_code == 401


# ===========================================================================
# GET /admin/login (HTML page)
# ===========================================================================


class TestAdminLoginPage:
    async def test_returns_html(self, client: AsyncClient, db_session: AsyncSession) -> None:
        """GET /admin/login returns an HTML page."""
        resp = await client.get("/admin/login")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]


# ===========================================================================
# GET /admin/dashboard (HTML page)
# ===========================================================================


class TestAdminDashboardPage:
    async def test_with_valid_cookie_returns_html(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Authenticated admin sees the dashboard HTML with accounts."""
        await _create_admin(db_session)
        await _seed_account(db_session)
        cookies = await _login(client)

        resp = await client.get("/admin/dashboard", cookies=cookies)
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        # Page should contain account data
        assert "1000-0001-0001" in resp.text

    async def test_without_cookie_redirects_to_login(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """No cookie redirects to /admin/login."""
        resp = await client.get("/admin/dashboard", follow_redirects=False)
        assert resp.status_code == 302
        assert "/admin/login" in resp.headers["location"]

    async def test_with_invalid_cookie_redirects_to_login(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """An expired/invalid cookie redirects to /admin/login."""
        resp = await client.get(
            "/admin/dashboard",
            cookies={"admin_session": "bogus-token"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "/admin/login" in resp.headers["location"]


# ===========================================================================
# GET /admin/audit-logs (HTML page)
# ===========================================================================


class TestAdminAuditLogsPage:
    async def test_with_valid_cookie_returns_html(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Authenticated admin sees the audit logs HTML page."""
        await _create_admin(db_session)
        await _seed_audit_logs(db_session)
        cookies = await _login(client)

        resp = await client.get("/admin/audit-logs", cookies=cookies)
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]

    async def test_without_cookie_redirects_to_login(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """No cookie redirects to /admin/login."""
        resp = await client.get("/admin/audit-logs", follow_redirects=False)
        assert resp.status_code == 302
        assert "/admin/login" in resp.headers["location"]
