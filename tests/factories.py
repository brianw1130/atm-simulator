"""Factory functions for generating test data.

Usage:
    customer = await create_test_customer(db_session)
    account = await create_test_account(db_session, customer_id=customer.id)
    card = await create_test_card(db_session, account_id=account.id, pin="1234")
"""

from datetime import date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.atm.config import settings
from src.atm.models.account import Account, AccountStatus, AccountType
from src.atm.models.card import ATMCard
from src.atm.models.customer import Customer
from src.atm.models.transaction import Transaction, TransactionType
from src.atm.utils.security import hash_pin

TEST_PEPPER = settings.pin_pepper

_customer_counter = 0


async def create_test_customer(
    session: AsyncSession,
    *,
    first_name: str = "Test",
    last_name: str = "User",
    date_of_birth: date | None = None,
    email: str | None = None,
    phone: str | None = None,
    is_active: bool = True,
) -> Customer:
    """Create and persist a test Customer."""
    global _customer_counter
    _customer_counter += 1
    if date_of_birth is None:
        date_of_birth = date(1990, 1, 15)
    if email is None:
        email = f"test{_customer_counter}@example.com"
    customer = Customer(
        first_name=first_name,
        last_name=last_name,
        date_of_birth=date_of_birth,
        email=email,
        phone=phone,
        is_active=is_active,
    )
    session.add(customer)
    await session.flush()
    return customer


async def create_test_account(
    session: AsyncSession,
    *,
    customer_id: int,
    account_number: str = "1000-0001-0001",
    account_type: AccountType = AccountType.CHECKING,
    balance_cents: int = 525_000,
    available_balance_cents: int | None = None,
    daily_withdrawal_used_cents: int = 0,
    daily_transfer_used_cents: int = 0,
    status: AccountStatus = AccountStatus.ACTIVE,
) -> Account:
    """Create and persist a test Account."""
    if available_balance_cents is None:
        available_balance_cents = balance_cents
    account = Account(
        customer_id=customer_id,
        account_number=account_number,
        account_type=account_type,
        balance_cents=balance_cents,
        available_balance_cents=available_balance_cents,
        daily_withdrawal_used_cents=daily_withdrawal_used_cents,
        daily_transfer_used_cents=daily_transfer_used_cents,
        status=status,
    )
    session.add(account)
    await session.flush()
    return account


async def create_test_card(
    session: AsyncSession,
    *,
    account_id: int,
    card_number: str = "4000-0000-0001",
    pin: str = "1234",
    failed_attempts: int = 0,
    locked_until: datetime | None = None,
    is_active: bool = True,
) -> ATMCard:
    """Create and persist a test ATMCard with the given PIN hashed."""
    pin_hashed = hash_pin(pin, TEST_PEPPER)
    card = ATMCard(
        account_id=account_id,
        card_number=card_number,
        pin_hash=pin_hashed,
        failed_attempts=failed_attempts,
        locked_until=locked_until,
        is_active=is_active,
    )
    session.add(card)
    await session.flush()
    return card


async def create_test_transaction(
    session: AsyncSession,
    *,
    account_id: int,
    transaction_type: TransactionType = TransactionType.WITHDRAWAL,
    amount_cents: int = 10_000,
    balance_after_cents: int = 515_000,
    reference_number: str = "REF-test-0001",
    description: str = "Test transaction",
    related_account_id: int | None = None,
    check_number: str | None = None,
    hold_until: datetime | None = None,
    metadata_json: dict | None = None,
) -> Transaction:
    """Create and persist a test Transaction."""
    txn = Transaction(
        account_id=account_id,
        transaction_type=transaction_type,
        amount_cents=amount_cents,
        balance_after_cents=balance_after_cents,
        reference_number=reference_number,
        description=description,
        related_account_id=related_account_id,
        check_number=check_number,
        hold_until=hold_until,
        metadata_json=metadata_json,
    )
    session.add(txn)
    await session.flush()
    return txn


async def seed_test_data(session: AsyncSession) -> dict:
    """Create the full seed dataset from CLAUDE.md.

    Returns:
        Dictionary keyed by name with created objects.
    """
    alice = await create_test_customer(
        session,
        first_name="Alice",
        last_name="Johnson",
        email="alice@example.com",
    )
    bob = await create_test_customer(
        session,
        first_name="Bob",
        last_name="Williams",
        email="bob@example.com",
    )
    charlie = await create_test_customer(
        session,
        first_name="Charlie",
        last_name="Davis",
        email="charlie@example.com",
    )

    alice_checking = await create_test_account(
        session,
        customer_id=alice.id,
        account_number="1000-0001-0001",
        account_type=AccountType.CHECKING,
        balance_cents=525_000,
    )
    alice_savings = await create_test_account(
        session,
        customer_id=alice.id,
        account_number="1000-0001-0002",
        account_type=AccountType.SAVINGS,
        balance_cents=1_250_000,
    )
    bob_checking = await create_test_account(
        session,
        customer_id=bob.id,
        account_number="1000-0002-0001",
        account_type=AccountType.CHECKING,
        balance_cents=85_075,
    )
    charlie_checking = await create_test_account(
        session,
        customer_id=charlie.id,
        account_number="1000-0003-0001",
        account_type=AccountType.CHECKING,
        balance_cents=0,
    )
    charlie_savings = await create_test_account(
        session,
        customer_id=charlie.id,
        account_number="1000-0003-0002",
        account_type=AccountType.SAVINGS,
        balance_cents=10_000,
    )

    alice_card = await create_test_card(
        session,
        account_id=alice_checking.id,
        card_number="4000-0001-0001",
        pin="7856",
    )
    bob_card = await create_test_card(
        session,
        account_id=bob_checking.id,
        card_number="4000-0002-0001",
        pin="5678",
    )
    charlie_card = await create_test_card(
        session,
        account_id=charlie_checking.id,
        card_number="4000-0003-0001",
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
    }
