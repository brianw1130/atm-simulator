"""Account service handling balance inquiries and account management.

Owner: Backend Engineer
Coverage requirement: 100%

Responsibilities:
    - Balance inquiry (available and total)
    - Mini-statement generation (last 5 transactions)
    - Daily limit tracking and reset
    - Account status checks
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.atm.models.account import Account, AccountStatus
from src.atm.models.audit import AuditEventType
from src.atm.models.transaction import Transaction
from src.atm.services.audit_service import log_event
from src.atm.utils.formatting import mask_account_number


class AccountError(Exception):
    """Raised for account-related errors."""


def _format_cents(cents: int) -> str:
    """Format an integer cents value as a dollar string.

    Args:
        cents: Amount in cents.

    Returns:
        Formatted string, e.g. "$1,234.56".
    """
    dollars = cents / 100
    return f"${dollars:,.2f}"


async def get_customer_accounts(
    session: AsyncSession,
    customer_id: int,
) -> list[Account]:
    """Retrieve all accounts belonging to a customer.

    Args:
        session: Async SQLAlchemy session.
        customer_id: The customer ID to look up.

    Returns:
        List of Account objects, possibly empty.
    """
    stmt = (
        select(Account)
        .where(Account.customer_id == customer_id)
        .where(Account.status != AccountStatus.CLOSED)
        .order_by(Account.account_number)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_account_balance(
    session: AsyncSession,
    account_id: int,
    session_id: str | None = None,
) -> dict[str, object]:
    """Get balance information and the last 5 transactions for an account.

    Args:
        session: Async SQLAlchemy session.
        account_id: The account to query.
        session_id: Optional session ID for audit logging.

    Returns:
        A dict containing:
            - account: account summary (masked number, type, balances, status)
            - recent_transactions: last 5 transactions with date, description,
              amount, and balance_after

    Raises:
        AccountError: If the account is not found.
    """
    stmt = select(Account).where(Account.id == account_id)
    result = await session.execute(stmt)
    account = result.scalars().first()

    if account is None:
        raise AccountError("Account not found")

    # Fetch last 5 transactions
    txn_stmt = (
        select(Transaction)
        .where(Transaction.account_id == account_id)
        .order_by(Transaction.created_at.desc())
        .limit(5)
    )
    txn_result = await session.execute(txn_stmt)
    transactions = list(txn_result.scalars().all())

    recent = []
    for txn in transactions:
        sign = "-" if txn.is_debit else "+"
        recent.append(
            {
                "date": txn.created_at,
                "description": txn.description,
                "amount": f"{sign}{_format_cents(txn.amount_cents)}",
                "balance_after": _format_cents(txn.balance_after_cents),
            }
        )

    await log_event(
        session,
        AuditEventType.BALANCE_INQUIRY,
        account_id=account_id,
        session_id=session_id,
    )

    return {
        "account": {
            "id": account.id,
            "account_number": mask_account_number(account.account_number),
            "account_type": account.account_type,
            "balance": _format_cents(account.balance_cents),
            "available_balance": _format_cents(account.available_balance_cents),
            "status": account.status,
        },
        "recent_transactions": recent,
    }
