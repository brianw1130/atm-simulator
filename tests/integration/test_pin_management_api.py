"""Integration tests for PIN management API endpoints.

Tests cover: successful PIN change, wrong current PIN, complexity failure,
PINs don't match.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import create_test_account, create_test_card, create_test_customer


async def _login(client: AsyncClient, card_number: str, pin: str) -> str:
    """Helper: login and return the session ID."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"card_number": card_number, "pin": pin},
    )
    assert resp.status_code == 200
    return resp.json()["session_id"]


async def _setup_alice(db_session: AsyncSession) -> None:
    """Seed Alice with checking account and card (PIN: 7856)."""
    customer = await create_test_customer(db_session, first_name="Alice", last_name="Johnson")
    account = await create_test_account(
        db_session,
        customer_id=customer.id,
        account_number="1000-0001-0001",
        balance_cents=525_000,
    )
    await create_test_card(
        db_session,
        account_id=account.id,
        card_number="4000-0001-0001",
        pin="7856",
    )
    await db_session.commit()


@pytest.mark.asyncio
async def test_successful_pin_change(client: AsyncClient, db_session: AsyncSession) -> None:
    """Change PIN successfully, then login with new PIN."""
    await _setup_alice(db_session)
    session_id = await _login(client, "4000-0001-0001", "7856")

    resp = await client.post(
        "/api/v1/auth/pin/change",
        json={
            "current_pin": "7856",
            "new_pin": "4829",
            "confirm_pin": "4829",
        },
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 200
    assert resp.json()["message"] == "PIN changed successfully"

    # Verify old PIN no longer works
    resp_old = await client.post(
        "/api/v1/auth/login",
        json={"card_number": "4000-0001-0001", "pin": "7856"},
    )
    assert resp_old.status_code == 401

    # Verify new PIN works
    resp_new = await client.post(
        "/api/v1/auth/login",
        json={"card_number": "4000-0001-0001", "pin": "4829"},
    )
    assert resp_new.status_code == 200


@pytest.mark.asyncio
async def test_pin_change_wrong_current_pin(client: AsyncClient, db_session: AsyncSession) -> None:
    """PIN change with incorrect current PIN returns 400."""
    await _setup_alice(db_session)
    session_id = await _login(client, "4000-0001-0001", "7856")

    resp = await client.post(
        "/api/v1/auth/pin/change",
        json={
            "current_pin": "0000",
            "new_pin": "4829",
            "confirm_pin": "4829",
        },
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 400
    assert "incorrect" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_pin_change_complexity_failure(client: AsyncClient, db_session: AsyncSession) -> None:
    """PIN change to sequential digits (1234) fails Pydantic validation (422)."""
    await _setup_alice(db_session)
    session_id = await _login(client, "4000-0001-0001", "7856")

    resp = await client.post(
        "/api/v1/auth/pin/change",
        json={
            "current_pin": "7856",
            "new_pin": "1234",
            "confirm_pin": "1234",
        },
        headers={"X-Session-ID": session_id},
    )

    # The PinChangeRequest schema validates new_pin complexity and rejects sequential
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_pin_change_confirmation_mismatch(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """PIN change where new_pin != confirm_pin fails validation (422)."""
    await _setup_alice(db_session)
    session_id = await _login(client, "4000-0001-0001", "7856")

    resp = await client.post(
        "/api/v1/auth/pin/change",
        json={
            "current_pin": "7856",
            "new_pin": "4829",
            "confirm_pin": "9999",
        },
        headers={"X-Session-ID": session_id},
    )

    assert resp.status_code == 422
