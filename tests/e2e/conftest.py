"""Shared fixtures and helpers for E2E tests.

Provides a seed_e2e_data function that creates the standard test dataset
with unique emails (avoiding UNIQUE constraint collisions across tests).
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.atm.models.account import AccountType
from tests.factories import create_test_account, create_test_card, create_test_customer


async def seed_e2e_data(session: AsyncSession) -> dict:
    """Create the full seed dataset with unique emails per invocation.

    Returns:
        Dictionary keyed by name with created objects and their IDs.
    """
    suffix = uuid.uuid4().hex[:8]

    alice = await create_test_customer(
        session,
        first_name="Alice",
        last_name="Johnson",
        email=f"alice_{suffix}@example.com",
    )
    bob = await create_test_customer(
        session,
        first_name="Bob",
        last_name="Williams",
        email=f"bob_{suffix}@example.com",
    )
    charlie = await create_test_customer(
        session,
        first_name="Charlie",
        last_name="Davis",
        email=f"charlie_{suffix}@example.com",
    )

    alice_checking = await create_test_account(
        session,
        customer_id=alice.id,
        account_number=f"1000-0001-{suffix[:4]}",
        account_type=AccountType.CHECKING,
        balance_cents=525_000,
    )
    alice_savings = await create_test_account(
        session,
        customer_id=alice.id,
        account_number=f"1001-0001-{suffix[:4]}",
        account_type=AccountType.SAVINGS,
        balance_cents=1_250_000,
    )
    bob_checking = await create_test_account(
        session,
        customer_id=bob.id,
        account_number=f"1000-0002-{suffix[:4]}",
        account_type=AccountType.CHECKING,
        balance_cents=85_075,
    )
    charlie_checking = await create_test_account(
        session,
        customer_id=charlie.id,
        account_number=f"1000-0003-{suffix[:4]}",
        account_type=AccountType.CHECKING,
        balance_cents=0,
    )
    charlie_savings = await create_test_account(
        session,
        customer_id=charlie.id,
        account_number=f"1001-0003-{suffix[:4]}",
        account_type=AccountType.SAVINGS,
        balance_cents=10_000,
    )

    alice_card = await create_test_card(
        session,
        account_id=alice_checking.id,
        card_number=f"4000-0001-{suffix[:4]}",
        pin="7856",
    )
    bob_card = await create_test_card(
        session,
        account_id=bob_checking.id,
        card_number=f"4000-0002-{suffix[:4]}",
        pin="5678",
    )
    charlie_card = await create_test_card(
        session,
        account_id=charlie_checking.id,
        card_number=f"4000-0003-{suffix[:4]}",
        pin="9012",
    )

    await session.commit()

    return {
        "alice": alice,
        "bob": bob,
        "charlie": charlie,
        "alice_checking": alice_checking,
        "alice_savings": alice_savings,
        "bob_checking": bob_checking,
        "charlie_checking": charlie_checking,
        "charlie_savings": charlie_savings,
        "alice_card": alice_card,
        "bob_card": bob_card,
        "charlie_card": charlie_card,
        # Convenience: card numbers for login
        "alice_card_number": f"4000-0001-{suffix[:4]}",
        "bob_card_number": f"4000-0002-{suffix[:4]}",
        "charlie_card_number": f"4000-0003-{suffix[:4]}",
        # Account numbers for transfers
        "alice_checking_number": f"1000-0001-{suffix[:4]}",
        "alice_savings_number": f"1001-0001-{suffix[:4]}",
        "bob_checking_number": f"1000-0002-{suffix[:4]}",
        "charlie_checking_number": f"1000-0003-{suffix[:4]}",
        "charlie_savings_number": f"1001-0003-{suffix[:4]}",
    }
