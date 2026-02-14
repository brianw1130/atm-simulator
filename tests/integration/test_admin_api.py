"""Integration tests for admin API endpoints.

Tests cover: login, logout, account listing, freeze/unfreeze, audit logs,
maintenance mode, customer CRUD, account CRUD, PIN reset, export/import,
and dashboard stats.
"""

from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.atm.models.audit import AuditEventType, AuditLog
from src.atm.services.admin_service import create_admin_user
from tests.factories import (
    create_test_account,
    create_test_card,
    create_test_customer,
)

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
# GET /admin/api/customers
# ===========================================================================


class TestListCustomers:
    async def test_returns_customers(self, client: AsyncClient, db_session: AsyncSession) -> None:
        """Authenticated admin can list all customers."""
        await _create_admin(db_session)
        await create_test_customer(
            db_session, first_name="Alice", last_name="Johnson", email="alice@test.com"
        )
        await db_session.commit()
        cookies = await _login(client)

        resp = await client.get("/admin/api/customers", cookies=cookies)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["first_name"] == "Alice"

    async def test_without_auth_returns_401(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Unauthenticated request returns 401."""
        resp = await client.get("/admin/api/customers")
        assert resp.status_code == 401


# ===========================================================================
# GET /admin/api/customers/{id}
# ===========================================================================


class TestGetCustomerDetail:
    async def test_returns_customer_detail(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Authenticated admin can get customer detail."""
        await _create_admin(db_session)
        customer = await create_test_customer(
            db_session, first_name="Alice", last_name="Johnson", email="alice@test.com"
        )
        account = await create_test_account(
            db_session, customer_id=customer.id, account_number="1000-0001-0001"
        )
        await create_test_card(db_session, account_id=account.id, card_number="1000-0001-0001")
        await db_session.commit()
        cookies = await _login(client)

        resp = await client.get(f"/admin/api/customers/{customer.id}", cookies=cookies)
        assert resp.status_code == 200
        data = resp.json()
        assert data["first_name"] == "Alice"
        assert len(data["accounts"]) == 1
        assert len(data["accounts"][0]["cards"]) == 1

    async def test_not_found_returns_404(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Nonexistent customer returns 404."""
        await _create_admin(db_session)
        cookies = await _login(client)
        resp = await client.get("/admin/api/customers/99999", cookies=cookies)
        assert resp.status_code == 404


# ===========================================================================
# POST /admin/api/customers
# ===========================================================================


class TestCreateCustomerEndpoint:
    async def test_creates_customer(self, client: AsyncClient, db_session: AsyncSession) -> None:
        """Authenticated admin can create a customer."""
        await _create_admin(db_session)
        cookies = await _login(client)

        resp = await client.post(
            "/admin/api/customers",
            json={
                "first_name": "New",
                "last_name": "Person",
                "date_of_birth": "1990-05-15",
                "email": "new@example.com",
                "phone": "555-0101",
            },
            cookies=cookies,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["first_name"] == "New"
        assert data["email"] == "new@example.com"
        assert data["account_count"] == 0

    async def test_duplicate_email_returns_409(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Creating a customer with a duplicate email returns 409."""
        await _create_admin(db_session)
        await create_test_customer(db_session, email="taken@example.com")
        await db_session.commit()
        cookies = await _login(client)

        resp = await client.post(
            "/admin/api/customers",
            json={
                "first_name": "Dup",
                "last_name": "Email",
                "date_of_birth": "1990-01-01",
                "email": "taken@example.com",
            },
            cookies=cookies,
        )
        assert resp.status_code == 409

    async def test_without_auth_returns_401(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Unauthenticated request returns 401."""
        resp = await client.post(
            "/admin/api/customers",
            json={
                "first_name": "No",
                "last_name": "Auth",
                "date_of_birth": "1990-01-01",
                "email": "no@example.com",
            },
        )
        assert resp.status_code == 401

    async def test_invalid_body_returns_422(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Invalid request body returns 422."""
        await _create_admin(db_session)
        cookies = await _login(client)

        resp = await client.post(
            "/admin/api/customers",
            json={"first_name": "Only"},
            cookies=cookies,
        )
        assert resp.status_code == 422


# ===========================================================================
# PUT /admin/api/customers/{id}
# ===========================================================================


class TestUpdateCustomerEndpoint:
    async def test_updates_customer(self, client: AsyncClient, db_session: AsyncSession) -> None:
        """Authenticated admin can update a customer."""
        await _create_admin(db_session)
        customer = await create_test_customer(db_session, first_name="Old", email="upd@example.com")
        await db_session.commit()
        cookies = await _login(client)

        resp = await client.put(
            f"/admin/api/customers/{customer.id}",
            json={"first_name": "New"},
            cookies=cookies,
        )
        assert resp.status_code == 200
        assert resp.json()["first_name"] == "New"

    async def test_not_found_returns_404(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Nonexistent customer returns 404."""
        await _create_admin(db_session)
        cookies = await _login(client)
        resp = await client.put(
            "/admin/api/customers/99999",
            json={"first_name": "X"},
            cookies=cookies,
        )
        assert resp.status_code == 404

    async def test_duplicate_email_returns_409(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Changing email to a duplicate returns 409."""
        await _create_admin(db_session)
        await create_test_customer(db_session, email="taken2@example.com")
        customer = await create_test_customer(db_session, email="mine2@example.com")
        await db_session.commit()
        cookies = await _login(client)

        resp = await client.put(
            f"/admin/api/customers/{customer.id}",
            json={"email": "taken2@example.com"},
            cookies=cookies,
        )
        assert resp.status_code == 409


# ===========================================================================
# POST /admin/api/customers/{id}/deactivate + activate
# ===========================================================================


class TestDeactivateCustomerEndpoint:
    async def test_deactivates_customer(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Authenticated admin can deactivate a customer."""
        await _create_admin(db_session)
        customer = await create_test_customer(db_session, email="deact@example.com")
        await db_session.commit()
        cookies = await _login(client)

        resp = await client.post(f"/admin/api/customers/{customer.id}/deactivate", cookies=cookies)
        assert resp.status_code == 200
        assert "deactivated" in resp.json()["message"].lower()

    async def test_not_found_returns_404(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Nonexistent customer returns 404."""
        await _create_admin(db_session)
        cookies = await _login(client)
        resp = await client.post("/admin/api/customers/99999/deactivate", cookies=cookies)
        assert resp.status_code == 404


class TestActivateCustomerEndpoint:
    async def test_activates_customer(self, client: AsyncClient, db_session: AsyncSession) -> None:
        """Authenticated admin can reactivate a customer."""
        await _create_admin(db_session)
        customer = await create_test_customer(db_session, is_active=False, email="act@example.com")
        await db_session.commit()
        cookies = await _login(client)

        resp = await client.post(f"/admin/api/customers/{customer.id}/activate", cookies=cookies)
        assert resp.status_code == 200
        assert "activated" in resp.json()["message"].lower()

    async def test_not_found_returns_404(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Nonexistent customer returns 404."""
        await _create_admin(db_session)
        cookies = await _login(client)
        resp = await client.post("/admin/api/customers/99999/activate", cookies=cookies)
        assert resp.status_code == 404


# ===========================================================================
# POST /admin/api/customers/{id}/accounts
# ===========================================================================


class TestCreateAccountEndpoint:
    async def test_creates_account(self, client: AsyncClient, db_session: AsyncSession) -> None:
        """Authenticated admin can create an account for a customer."""
        await _create_admin(db_session)
        customer = await create_test_customer(db_session, email="newacct@example.com")
        await db_session.commit()
        cookies = await _login(client)

        resp = await client.post(
            f"/admin/api/customers/{customer.id}/accounts",
            json={"account_type": "CHECKING", "initial_balance_cents": 50000},
            cookies=cookies,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["account_type"] == "CHECKING"
        assert data["balance"] == "$500.00"
        assert len(data["cards"]) == 1

    async def test_customer_not_found_returns_404(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Creating account for nonexistent customer returns 404."""
        await _create_admin(db_session)
        cookies = await _login(client)

        resp = await client.post(
            "/admin/api/customers/99999/accounts",
            json={"account_type": "CHECKING"},
            cookies=cookies,
        )
        assert resp.status_code == 404

    async def test_without_auth_returns_401(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Unauthenticated request returns 401."""
        resp = await client.post(
            "/admin/api/customers/1/accounts",
            json={"account_type": "CHECKING"},
        )
        assert resp.status_code == 401

    async def test_invalid_type_returns_422(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Invalid account type returns 422."""
        await _create_admin(db_session)
        customer = await create_test_customer(db_session, email="badtype@example.com")
        await db_session.commit()
        cookies = await _login(client)

        resp = await client.post(
            f"/admin/api/customers/{customer.id}/accounts",
            json={"account_type": "INVALID"},
            cookies=cookies,
        )
        assert resp.status_code == 422


# ===========================================================================
# PUT /admin/api/accounts/{id}
# ===========================================================================


class TestUpdateAccountEndpoint:
    async def test_updates_account(self, client: AsyncClient, db_session: AsyncSession) -> None:
        """Authenticated admin can update account limits."""
        await _create_admin(db_session)
        account_id = await _seed_account(db_session)
        cookies = await _login(client)

        resp = await client.put(
            f"/admin/api/accounts/{account_id}",
            json={"daily_withdrawal_limit_cents": 100000},
            cookies=cookies,
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == account_id

    async def test_not_found_returns_404(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Nonexistent account returns 404."""
        await _create_admin(db_session)
        cookies = await _login(client)
        resp = await client.put(
            "/admin/api/accounts/99999",
            json={"daily_withdrawal_limit_cents": 100000},
            cookies=cookies,
        )
        assert resp.status_code == 404


# ===========================================================================
# POST /admin/api/accounts/{id}/close
# ===========================================================================


class TestCloseAccountEndpoint:
    async def test_closes_zero_balance_account(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Authenticated admin can close an account with zero balance."""
        await _create_admin(db_session)
        customer = await create_test_customer(db_session, email="close@example.com")
        account = await create_test_account(
            db_session,
            customer_id=customer.id,
            account_number="1000-9001-0001",
            balance_cents=0,
        )
        await db_session.commit()
        cookies = await _login(client)

        resp = await client.post(f"/admin/api/accounts/{account.id}/close", cookies=cookies)
        assert resp.status_code == 200
        assert "closed" in resp.json()["message"].lower()

    async def test_non_zero_balance_returns_400(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Cannot close an account with a non-zero balance."""
        await _create_admin(db_session)
        account_id = await _seed_account(db_session)  # has 525000 balance
        cookies = await _login(client)

        resp = await client.post(f"/admin/api/accounts/{account_id}/close", cookies=cookies)
        assert resp.status_code == 400
        assert "non-zero" in resp.json()["detail"].lower()

    async def test_not_found_returns_404(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Nonexistent account returns 404."""
        await _create_admin(db_session)
        cookies = await _login(client)
        resp = await client.post("/admin/api/accounts/99999/close", cookies=cookies)
        assert resp.status_code == 404


# ===========================================================================
# POST /admin/api/cards/{id}/reset-pin
# ===========================================================================


class TestResetPinEndpoint:
    async def test_resets_pin(self, client: AsyncClient, db_session: AsyncSession) -> None:
        """Authenticated admin can reset a card's PIN."""
        await _create_admin(db_session)
        customer = await create_test_customer(db_session, email="pin@example.com")
        account = await create_test_account(
            db_session,
            customer_id=customer.id,
            account_number="1000-6001-0001",
        )
        card = await create_test_card(
            db_session, account_id=account.id, card_number="1000-6001-0001"
        )
        await db_session.commit()
        cookies = await _login(client)

        resp = await client.post(
            f"/admin/api/cards/{card.id}/reset-pin",
            json={"new_pin": "4829"},
            cookies=cookies,
        )
        assert resp.status_code == 200
        assert "reset" in resp.json()["message"].lower()

    async def test_weak_pin_returns_422(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """A weak PIN returns 422."""
        await _create_admin(db_session)
        customer = await create_test_customer(db_session, email="weakpin@example.com")
        account = await create_test_account(
            db_session,
            customer_id=customer.id,
            account_number="1000-6002-0001",
        )
        card = await create_test_card(
            db_session, account_id=account.id, card_number="1000-6002-0001"
        )
        await db_session.commit()
        cookies = await _login(client)

        resp = await client.post(
            f"/admin/api/cards/{card.id}/reset-pin",
            json={"new_pin": "1111"},
            cookies=cookies,
        )
        assert resp.status_code == 422

    async def test_not_found_returns_404(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Nonexistent card returns 404."""
        await _create_admin(db_session)
        cookies = await _login(client)
        resp = await client.post(
            "/admin/api/cards/99999/reset-pin",
            json={"new_pin": "4829"},
            cookies=cookies,
        )
        assert resp.status_code == 404

    async def test_without_auth_returns_401(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Unauthenticated request returns 401."""
        resp = await client.post(
            "/admin/api/cards/1/reset-pin",
            json={"new_pin": "4829"},
        )
        assert resp.status_code == 401


# ===========================================================================
# Export / Import endpoints
# ===========================================================================


class TestExportEndpoint:
    async def test_export_returns_json_download(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """GET /api/export returns JSON with content-disposition header."""
        await _create_admin(db_session)
        await _seed_account(db_session)
        cookies = await _login(client)

        resp = await client.get("/admin/api/export", cookies=cookies)
        assert resp.status_code == 200
        assert "attachment" in resp.headers.get("content-disposition", "")
        data = resp.json()
        assert data["version"] == "1.0"
        assert "customers" in data
        assert "admin_users" in data

    async def test_export_without_auth_returns_401(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Unauthenticated export returns 401."""
        resp = await client.get("/admin/api/export")
        assert resp.status_code == 401


class TestImportEndpoint:
    async def test_import_success(self, client: AsyncClient, db_session: AsyncSession) -> None:
        """POST /api/import with valid JSON creates entities."""
        await _create_admin(db_session)
        cookies = await _login(client)

        import json

        snapshot = {
            "version": "1.0",
            "exported_at": "2026-02-14T00:00:00Z",
            "customers": [
                {
                    "first_name": "Import",
                    "last_name": "Test",
                    "date_of_birth": "1990-01-01",
                    "email": "import-integ@example.com",
                    "is_active": True,
                    "accounts": [
                        {
                            "account_number": "1000-9099-0001",
                            "account_type": "CHECKING",
                            "balance_cents": 50000,
                            "available_balance_cents": 50000,
                            "status": "ACTIVE",
                            "cards": [],
                        }
                    ],
                }
            ],
            "admin_users": [],
        }
        file_content = json.dumps(snapshot).encode()

        resp = await client.post(
            "/admin/api/import?conflict_strategy=skip",
            files={"file": ("snapshot.json", file_content, "application/json")},
            cookies=cookies,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["customers_created"] == 1
        assert data["accounts_created"] == 1

    async def test_import_without_auth_returns_401(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Unauthenticated import returns 401."""
        resp = await client.post(
            "/admin/api/import",
            files={"file": ("snapshot.json", b"{}", "application/json")},
        )
        assert resp.status_code == 401

    async def test_import_invalid_json_returns_422(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Invalid JSON file returns 422."""
        await _create_admin(db_session)
        cookies = await _login(client)

        resp = await client.post(
            "/admin/api/import",
            files={"file": ("bad.json", b"not json!", "application/json")},
            cookies=cookies,
        )
        assert resp.status_code == 422

    async def test_import_malformed_snapshot_returns_422(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Valid JSON without required keys returns 422."""
        await _create_admin(db_session)
        cookies = await _login(client)

        import json

        resp = await client.post(
            "/admin/api/import",
            files={"file": ("bad.json", json.dumps({"foo": "bar"}).encode(), "application/json")},
            cookies=cookies,
        )
        assert resp.status_code == 422

    async def test_import_invalid_conflict_strategy_returns_422(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Invalid conflict_strategy returns 422."""
        await _create_admin(db_session)
        cookies = await _login(client)

        import json

        snapshot = json.dumps({"version": "1.0", "customers": [], "admin_users": []}).encode()
        resp = await client.post(
            "/admin/api/import?conflict_strategy=invalid",
            files={"file": ("snapshot.json", snapshot, "application/json")},
            cookies=cookies,
        )
        assert resp.status_code == 422

    async def test_export_import_round_trip(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Export then re-import with skip produces zero creates."""
        await _create_admin(db_session)
        await _seed_account(db_session)
        cookies = await _login(client)

        # Export
        export_resp = await client.get("/admin/api/export", cookies=cookies)
        assert export_resp.status_code == 200
        snapshot_bytes = export_resp.content

        # Re-import with skip
        import_resp = await client.post(
            "/admin/api/import?conflict_strategy=skip",
            files={"file": ("snapshot.json", snapshot_bytes, "application/json")},
            cookies=cookies,
        )
        assert import_resp.status_code == 200
        data = import_resp.json()
        assert data["customers_skipped"] >= 1
        assert data["customers_created"] == 0

    async def test_export_calls_s3_upload(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Export endpoint also calls upload_snapshot for S3 persistence."""
        await _create_admin(db_session)
        await _seed_account(db_session)
        cookies = await _login(client)

        with patch("src.atm.services.s3_client.upload_snapshot") as mock_upload:
            mock_upload.return_value = True
            resp = await client.get("/admin/api/export", cookies=cookies)

        assert resp.status_code == 200
        mock_upload.assert_called_once()
        args = mock_upload.call_args
        assert args[0][0]["version"] == "1.0"  # snapshot dict
        assert args[0][1].startswith("atm-snapshot-")  # filename

    async def test_export_succeeds_when_s3_fails(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Export still returns 200 when S3 upload raises an exception."""
        await _create_admin(db_session)
        await _seed_account(db_session)
        cookies = await _login(client)

        with patch(
            "src.atm.services.s3_client.upload_snapshot",
            side_effect=RuntimeError("S3 unavailable"),
        ):
            resp = await client.get("/admin/api/export", cookies=cookies)

        assert resp.status_code == 200
        data = resp.json()
        assert data["version"] == "1.0"


# ===========================================================================
# GET /admin/api/dashboard-stats
# ===========================================================================


class TestDashboardStats:
    async def test_returns_stats(self, client: AsyncClient, db_session: AsyncSession) -> None:
        """Dashboard stats endpoint returns correct counts."""
        await _create_admin(db_session)
        customer = await create_test_customer(
            db_session, first_name="Alice", email="stats@example.com"
        )
        await create_test_account(
            db_session,
            customer_id=customer.id,
            account_number="1000-8001-0001",
            balance_cents=100_000,
        )
        await db_session.commit()
        cookies = await _login(client)

        resp = await client.get("/admin/api/dashboard-stats", cookies=cookies)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_customers"] >= 1
        assert data["active_customers"] >= 1
        assert data["total_accounts"] >= 1
        assert data["active_accounts"] >= 1
        assert "total_balance_formatted" in data

    async def test_without_auth_returns_401(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Unauthenticated request returns 401."""
        resp = await client.get("/admin/api/dashboard-stats")
        assert resp.status_code == 401


# ===========================================================================
# GET /admin/api/accounts?customer_id=
# ===========================================================================


class TestListAccountsFilter:
    async def test_filter_by_customer_id(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Accounts can be filtered by customer_id query parameter."""
        await _create_admin(db_session)
        alice = await create_test_customer(
            db_session, first_name="Alice", email="filter-a@example.com"
        )
        bob = await create_test_customer(db_session, first_name="Bob", email="filter-b@example.com")
        await create_test_account(
            db_session,
            customer_id=alice.id,
            account_number="1000-7001-0001",
            balance_cents=100_000,
        )
        await create_test_account(
            db_session,
            customer_id=bob.id,
            account_number="1000-7002-0001",
            balance_cents=50_000,
        )
        await db_session.commit()
        cookies = await _login(client)

        resp = await client.get(
            "/admin/api/accounts",
            params={"customer_id": alice.id},
            cookies=cookies,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["account_number"] == "1000-7001-0001"


# ===========================================================================
# GET /admin/api/audit-logs?account_id=
# ===========================================================================


class TestAuditLogsAccountFilter:
    async def test_filter_by_account_id(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Audit logs can be filtered by account_id query parameter."""
        await _create_admin(db_session)
        account_id = await _seed_account(db_session)
        # Create logs with and without account_id
        db_session.add(
            AuditLog(
                event_type=AuditEventType.WITHDRAWAL,
                account_id=account_id,
                details={"amount": 10000},
            )
        )
        db_session.add(
            AuditLog(
                event_type=AuditEventType.LOGIN_SUCCESS,
                details={"card": "***0001"},
            )
        )
        await db_session.flush()
        await db_session.commit()
        cookies = await _login(client)

        resp = await client.get(
            "/admin/api/audit-logs",
            params={"account_id": account_id},
            cookies=cookies,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert all(log["account_id"] == account_id for log in data)
