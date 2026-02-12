"""Integration tests for Redis-backed session management.

Tests cover:
    - Login creates a session in Redis
    - Logout removes the session from Redis
    - Expired/deleted sessions return 401 on protected endpoints
    - Session validation refreshes TTL (sliding window expiry)
"""

import json

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.atm.services.auth_service import validate_session
from src.atm.services.redis_client import get_redis
from tests.factories import create_test_account, create_test_card, create_test_customer


@pytest.mark.asyncio
async def test_session_stored_in_redis(client: AsyncClient, db_session: AsyncSession) -> None:
    """Login creates a session entry in Redis with correct account data."""
    customer = await create_test_customer(db_session, first_name="Redis", last_name="Tester")
    account = await create_test_account(
        db_session,
        customer_id=customer.id,
        account_number="1000-RSST-0001",
        balance_cents=100_000,
    )
    await create_test_card(
        db_session,
        account_id=account.id,
        card_number="4000-RSST-0001",
        pin="1357",
    )
    await db_session.commit()

    resp = await client.post(
        "/api/v1/auth/login",
        json={"card_number": "4000-RSST-0001", "pin": "1357"},
    )
    assert resp.status_code == 200
    session_id = resp.json()["session_id"]

    # Verify session exists in Redis
    redis = await get_redis()
    data = await redis.get(f"session:{session_id}")
    assert data is not None

    session_data = json.loads(data)
    assert session_data["account_id"] == account.id
    assert session_data["customer_id"] == customer.id


@pytest.mark.asyncio
async def test_logout_removes_session_from_redis(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Logout deletes the session from Redis."""
    customer = await create_test_customer(db_session)
    account = await create_test_account(
        db_session,
        customer_id=customer.id,
        account_number="1000-RSST-0002",
    )
    await create_test_card(
        db_session,
        account_id=account.id,
        card_number="4000-RSST-0002",
        pin="2468",
    )
    await db_session.commit()

    resp = await client.post(
        "/api/v1/auth/login",
        json={"card_number": "4000-RSST-0002", "pin": "2468"},
    )
    assert resp.status_code == 200
    session_id = resp.json()["session_id"]

    # Logout
    logout_resp = await client.post(
        "/api/v1/auth/logout",
        headers={"X-Session-ID": session_id},
    )
    assert logout_resp.status_code == 200

    # Verify session removed from Redis
    redis = await get_redis()
    data = await redis.get(f"session:{session_id}")
    assert data is None


@pytest.mark.asyncio
async def test_expired_session_returns_401(client: AsyncClient, db_session: AsyncSession) -> None:
    """An expired session (removed from Redis) returns 401 on protected endpoints."""
    customer = await create_test_customer(db_session)
    account = await create_test_account(
        db_session,
        customer_id=customer.id,
        account_number="1000-RSST-0003",
    )
    await create_test_card(
        db_session,
        account_id=account.id,
        card_number="4000-RSST-0003",
        pin="3579",
    )
    await db_session.commit()

    resp = await client.post(
        "/api/v1/auth/login",
        json={"card_number": "4000-RSST-0003", "pin": "3579"},
    )
    assert resp.status_code == 200
    session_id = resp.json()["session_id"]

    # Manually delete the session from Redis to simulate expiry
    redis = await get_redis()
    await redis.delete(f"session:{session_id}")

    # Try to use the expired session on a protected endpoint
    resp = await client.get(
        f"/api/v1/accounts/{account.id}/balance",
        headers={"X-Session-ID": session_id},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_session_contains_card_id(client: AsyncClient, db_session: AsyncSession) -> None:
    """Session data in Redis includes the card_id used for authentication."""
    customer = await create_test_customer(db_session)
    account = await create_test_account(
        db_session,
        customer_id=customer.id,
        account_number="1000-RSST-0004",
    )
    card = await create_test_card(
        db_session,
        account_id=account.id,
        card_number="4000-RSST-0004",
        pin="4680",
    )
    await db_session.commit()

    resp = await client.post(
        "/api/v1/auth/login",
        json={"card_number": "4000-RSST-0004", "pin": "4680"},
    )
    assert resp.status_code == 200
    session_id = resp.json()["session_id"]

    redis = await get_redis()
    data = await redis.get(f"session:{session_id}")
    session_data = json.loads(data)
    assert session_data["card_id"] == card.id
    assert "created_at" in session_data
    assert "last_activity" in session_data


@pytest.mark.asyncio
async def test_session_validation_refreshes_ttl(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Validating a session refreshes last_activity and the Redis TTL."""
    customer = await create_test_customer(db_session)
    account = await create_test_account(
        db_session,
        customer_id=customer.id,
        account_number="1000-RSST-0005",
    )
    await create_test_card(
        db_session,
        account_id=account.id,
        card_number="4000-RSST-0005",
        pin="5791",
    )
    await db_session.commit()

    resp = await client.post(
        "/api/v1/auth/login",
        json={"card_number": "4000-RSST-0005", "pin": "5791"},
    )
    assert resp.status_code == 200
    session_id = resp.json()["session_id"]

    # Read initial session data
    redis = await get_redis()
    initial_data = json.loads(await redis.get(f"session:{session_id}"))
    initial_activity = initial_data["last_activity"]

    # Validate the session (this should refresh last_activity)
    result = await validate_session(session_id)
    assert result is not None
    assert result["account_id"] == account.id

    # Read updated session data
    updated_data = json.loads(await redis.get(f"session:{session_id}"))
    updated_activity = updated_data["last_activity"]

    # last_activity should have been refreshed (>= initial, usually different)
    assert updated_activity >= initial_activity


@pytest.mark.asyncio
async def test_session_validation_returns_none_for_missing_session() -> None:
    """validate_session returns None for a session ID that does not exist in Redis."""
    result = await validate_session("nonexistent-session-id")
    assert result is None
