"""E2E tests for cross-feature compound journeys.

E2E-CMP-01 and E2E-CMP-04 as specified in CLAUDE.md.
Each test is independent with fresh database state.
"""

import os
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.atm.models.account import Account
from tests.e2e.conftest import seed_e2e_data
from tests.factories import create_test_card


async def _login(client: AsyncClient, card_number: str, pin: str) -> str:
    """Helper: login and return the session ID."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"card_number": card_number, "pin": pin},
    )
    assert resp.status_code == 200
    return resp.json()["session_id"]


@pytest.mark.asyncio
async def test_e2e_cmp_01_full_session_lifecycle(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """E2E-CMP-01: Full Session Lifecycle."""
    data = await seed_e2e_data(db_session)
    session_id = await _login(client, data["alice_card_number"], "7856")

    # Check balance
    bal_resp = await client.get(
        f"/api/v1/accounts/{data['alice_checking'].id}/balance",
        headers={"X-Session-ID": session_id},
    )
    assert bal_resp.status_code == 200
    assert bal_resp.json()["account"]["balance"] == "$5,250.00"

    # Withdraw $100
    w_resp = await client.post(
        "/api/v1/transactions/withdraw",
        json={"amount_cents": 10_000},
        headers={"X-Session-ID": session_id},
    )
    assert w_resp.status_code == 201
    assert w_resp.json()["balance_after"] == "$5,150.00"

    # Transfer $50 to savings
    t_resp = await client.post(
        "/api/v1/transactions/transfer",
        json={
            "destination_account_number": data["alice_savings_number"],
            "amount_cents": 5_000,
        },
        headers={"X-Session-ID": session_id},
    )
    assert t_resp.status_code == 201
    assert t_resp.json()["balance_after"] == "$5,100.00"

    # Check balance again
    bal_resp2 = await client.get(
        f"/api/v1/accounts/{data['alice_checking'].id}/balance",
        headers={"X-Session-ID": session_id},
    )
    assert bal_resp2.status_code == 200
    assert bal_resp2.json()["account"]["balance"] == "$5,100.00"
    assert len(bal_resp2.json()["recent_transactions"]) >= 2

    # Generate statement
    stmt_resp = await client.post(
        "/api/v1/statements/generate",
        json={"days": 7},
        headers={"X-Session-ID": session_id},
    )
    assert stmt_resp.status_code == 200
    stmt_data = stmt_resp.json()
    assert stmt_data["transaction_count"] >= 2
    assert stmt_data["closing_balance"] == "$5,100.00"
    assert os.path.exists(stmt_data["file_path"])

    # Logout
    logout_resp = await client.post(
        "/api/v1/auth/logout",
        headers={"X-Session-ID": session_id},
    )
    assert logout_resp.status_code == 200

    # Verify session terminated
    post_logout_resp = await client.get(
        f"/api/v1/accounts/{data['alice_checking'].id}/balance",
        headers={"X-Session-ID": session_id},
    )
    assert post_logout_resp.status_code == 401


@pytest.mark.asyncio
async def test_e2e_cmp_04_multi_account_customer_journey(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """E2E-CMP-04: Multi-Account Customer Journey."""
    data = await seed_e2e_data(db_session)

    savings_card_number = f"4001-0001-{uuid.uuid4().hex[:4]}"
    await create_test_card(
        db_session,
        account_id=data["alice_savings"].id,
        card_number=savings_card_number,
        pin="7856",
    )
    await db_session.commit()

    session_id = await _login(client, data["alice_card_number"], "7856")

    # Check checking balance
    checking_bal = await client.get(
        f"/api/v1/accounts/{data['alice_checking'].id}/balance",
        headers={"X-Session-ID": session_id},
    )
    assert checking_bal.status_code == 200
    assert checking_bal.json()["account"]["balance"] == "$5,250.00"

    # Check savings balance
    savings_bal = await client.get(
        f"/api/v1/accounts/{data['alice_savings'].id}/balance",
        headers={"X-Session-ID": session_id},
    )
    assert savings_bal.status_code == 200
    assert savings_bal.json()["account"]["balance"] == "$12,500.00"

    # Transfer $500 checking -> savings
    t_resp = await client.post(
        "/api/v1/transactions/transfer",
        json={
            "destination_account_number": data["alice_savings_number"],
            "amount_cents": 50_000,
        },
        headers={"X-Session-ID": session_id},
    )
    assert t_resp.status_code == 201
    assert t_resp.json()["balance_after"] == "$4,750.00"

    # Withdraw $200 from checking
    w_resp = await client.post(
        "/api/v1/transactions/withdraw",
        json={"amount_cents": 20_000},
        headers={"X-Session-ID": session_id},
    )
    assert w_resp.status_code == 201
    assert w_resp.json()["balance_after"] == "$4,550.00"

    # Verify final database state
    checking_stmt = select(Account).where(Account.id == data["alice_checking"].id)
    checking = (await db_session.execute(checking_stmt)).scalars().first()
    assert checking is not None
    assert checking.balance_cents == 455_000

    savings_stmt = select(Account).where(Account.id == data["alice_savings"].id)
    savings = (await db_session.execute(savings_stmt)).scalars().first()
    assert savings is not None
    assert savings.balance_cents == 1_300_000

    # Generate statement for checking
    stmt_resp = await client.post(
        "/api/v1/statements/generate",
        json={"days": 7},
        headers={"X-Session-ID": session_id},
    )
    assert stmt_resp.status_code == 200
    stmt_data = stmt_resp.json()
    assert stmt_data["transaction_count"] == 2
    assert stmt_data["closing_balance"] == "$4,550.00"
