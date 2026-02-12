"""Statement service handling PDF statement generation.

Owner: Backend Engineer + UX Designer (layout)
Coverage requirement: 100%

Responsibilities:
    - Query transactions for date range
    - Calculate opening and closing balances
    - Generate PDF via ReportLab
    - File management for generated statements
"""

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.atm.config import settings
from src.atm.models.account import Account
from src.atm.models.audit import AuditEventType
from src.atm.models.transaction import Transaction
from src.atm.pdf.statement_generator import generate_statement_pdf
from src.atm.services.audit_service import log_event
from src.atm.utils.formatting import mask_account_number


def _utcnow() -> datetime:
    """Return current UTC time as a naive datetime for DB compatibility.

    Returns:
        A naive datetime representing the current UTC time.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


class StatementError(Exception):
    """Raised when statement generation fails."""


def _format_cents(cents: int) -> str:
    """Format an integer cents value as a dollar string.

    Args:
        cents: Amount in cents.

    Returns:
        Formatted string, e.g. "$1,234.56".
    """
    dollars = cents / 100
    return f"${dollars:,.2f}"


async def generate_statement(
    session: AsyncSession,
    account_id: int,
    days: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    session_id: str | None = None,
) -> dict[str, object]:
    """Generate a PDF account statement for a date range.

    Determines the date range from either a relative number of days or
    explicit start/end dates. Queries all transactions in the range,
    calculates opening and closing balances, and generates a PDF.

    Args:
        session: Async SQLAlchemy session.
        account_id: The account to generate a statement for.
        days: Number of days to include (used if start_date/end_date not given).
        start_date: Custom range start date (inclusive).
        end_date: Custom range end date (inclusive).
        session_id: Optional session ID for audit logging.

    Returns:
        A dict compatible with StatementResponse containing file_path,
        period, transaction_count, opening_balance, and closing_balance.

    Raises:
        StatementError: If the account is not found or dates are invalid.
    """
    # Load account with customer info (eager-load customer to avoid async lazy load)
    stmt = (
        select(Account)
        .options(selectinload(Account.customer))
        .where(Account.id == account_id)
    )
    result = await session.execute(stmt)
    account = result.scalars().first()

    if account is None:
        raise StatementError("Account not found")

    # Load customer via relationship
    customer = account.customer

    # Determine date range (naive UTC for SQLite compatibility)
    now = _utcnow()
    if start_date is not None and end_date is not None:
        range_start = datetime(
            start_date.year, start_date.month, start_date.day,
        )
        range_end = datetime(
            end_date.year, end_date.month, end_date.day,
            hour=23, minute=59, second=59, microsecond=999999,
        )
    else:
        period_days = days if days is not None else 30
        range_start = now - timedelta(days=period_days)
        range_end = now

    # Query transactions in range, ordered chronologically
    txn_stmt = (
        select(Transaction)
        .where(
            and_(
                Transaction.account_id == account_id,
                Transaction.created_at >= range_start,
                Transaction.created_at <= range_end,
            )
        )
        .order_by(Transaction.created_at.asc())
    )
    txn_result = await session.execute(txn_stmt)
    transactions = list(txn_result.scalars().all())

    # Calculate opening balance: closing balance minus net effect of all transactions
    closing_balance_cents = account.balance_cents
    net_effect = 0
    for txn in transactions:
        if txn.is_debit:
            net_effect -= txn.amount_cents
        else:
            net_effect += txn.amount_cents
    opening_balance_cents = closing_balance_cents - net_effect

    # Build transaction data for PDF
    txn_data: list[dict[str, object]] = []
    for txn in transactions:
        txn_data.append({
            "date": txn.created_at,
            "description": txn.description,
            "amount_cents": txn.amount_cents,
            "balance_after_cents": txn.balance_after_cents,
            "is_debit": txn.is_debit,
        })

    # Format period string
    period_str = (
        f"{range_start.strftime('%b %d, %Y')} - {range_end.strftime('%b %d, %Y')}"
    )

    # Generate file path
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    masked = mask_account_number(account.account_number)
    filename = f"statement_{masked}_{timestamp}.pdf"
    file_path = f"{settings.statement_output_dir}/{filename}"

    # Generate PDF
    account_info = {
        "customer_name": customer.full_name,
        "account_number": masked,
        "account_type": account.account_type.value,
    }
    generate_statement_pdf(
        file_path=file_path,
        account_info=account_info,
        transactions=txn_data,
        period=period_str,
        opening_balance_cents=opening_balance_cents,
        closing_balance_cents=closing_balance_cents,
    )

    await log_event(
        session,
        AuditEventType.STATEMENT_GENERATED,
        account_id=account_id,
        session_id=session_id,
        details={
            "period": period_str,
            "transaction_count": len(transactions),
            "file_path": file_path,
        },
    )

    return {
        "file_path": file_path,
        "period": period_str,
        "transaction_count": len(transactions),
        "opening_balance": _format_cents(opening_balance_cents),
        "closing_balance": _format_cents(closing_balance_cents),
    }
