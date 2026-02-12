"""Factory functions for generating test data.

Usage:
    customer = await create_test_customer(db_session)
    account = await create_test_account(db_session, customer_id=customer.id)
    card = await create_test_card(db_session, account_id=account.id, pin="1234")
"""

# TODO: Implement factory functions:
# - create_test_customer(session, **overrides) -> Customer
# - create_test_account(session, customer_id, **overrides) -> Account
# - create_test_card(session, account_id, pin, **overrides) -> ATMCard
# - create_test_transaction(session, account_id, **overrides) -> Transaction
# - seed_test_data(session) -> dict  # Creates the full seed dataset from CLAUDE.md
