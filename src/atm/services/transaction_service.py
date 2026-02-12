"""Transaction service handling withdrawals, deposits, and transfers.

Owner: Backend Engineer
Coverage requirement: 100%

Responsibilities:
    - Cash withdrawal with denomination validation ($20 multiples)
    - Cash deposit with hold policy (first $200 immediate, remainder 1 business day)
    - Check deposit with extended hold (first $200 next business day, remainder 2 business days)
    - Fund transfers (own accounts and external)
    - Daily limit enforcement
    - Overdraft protection
    - Reference number generation
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.atm.config import settings
from src.atm.models.account import Account, AccountStatus
from src.atm.models.audit import AuditEventType
from src.atm.models.transaction import Transaction, TransactionType
from src.atm.services.audit_service import log_event
from src.atm.services.cassette_service import can_dispense, dispense_bills
from src.atm.utils.formatting import mask_account_number
from src.atm.utils.security import generate_reference_number


def _utcnow() -> datetime:
    """Return current UTC time as a naive datetime for DB compatibility.

    Returns:
        A naive datetime representing the current UTC time.
    """
    return datetime.now(UTC).replace(tzinfo=None)


# Denomination constants (in cents)
TWENTY_DOLLAR_BILL_CENTS = 2_000
IMMEDIATE_AVAILABILITY_THRESHOLD_CENTS = 20_000  # $200


class TransactionError(Exception):
    """Raised when a transaction fails validation or business rules."""


class InsufficientFundsError(TransactionError):
    """Raised when the account has insufficient funds for the operation."""


class DailyLimitExceededError(TransactionError):
    """Raised when a transaction would exceed a daily limit."""


class AccountFrozenError(TransactionError):
    """Raised when an operation is attempted on a frozen account."""


def _format_cents(cents: int) -> str:
    """Format an integer cents value as a dollar string.

    Args:
        cents: Amount in cents.

    Returns:
        Formatted string, e.g. "$1,234.56".
    """
    dollars = cents / 100
    return f"${dollars:,.2f}"


def _next_business_day(from_date: datetime, days: int = 1) -> datetime:
    """Calculate a future business day (skipping weekends).

    Args:
        from_date: The starting datetime.
        days: Number of business days to advance.

    Returns:
        A datetime on the target business day, preserving the time component.
    """
    current = from_date
    remaining = days
    while remaining > 0:
        current += timedelta(days=1)
        # Monday=0, Sunday=6; weekdays are 0-4
        if current.weekday() < 5:
            remaining -= 1
    return current


async def _load_account(
    session: AsyncSession,
    account_id: int,
) -> Account:
    """Load an account and validate it is active.

    Args:
        session: Async SQLAlchemy session.
        account_id: The account ID to load.

    Returns:
        The Account object.

    Raises:
        TransactionError: If the account is not found.
        AccountFrozenError: If the account is frozen or closed.
    """
    stmt = select(Account).where(Account.id == account_id)
    result = await session.execute(stmt)
    account = result.scalars().first()

    if account is None:
        raise TransactionError("Account not found")

    if account.status == AccountStatus.FROZEN:
        raise AccountFrozenError("Account is frozen. Operations are not permitted.")

    if account.status == AccountStatus.CLOSED:
        raise AccountFrozenError("Account is closed. Operations are not permitted.")

    return account


async def withdraw(
    session: AsyncSession,
    account_id: int,
    amount_cents: int,
    session_id: str | None = None,
) -> dict[str, object]:
    """Process a cash withdrawal.

    Validates the amount is a multiple of $20, checks sufficient available
    balance, enforces the daily withdrawal limit, and updates the account.

    Args:
        session: Async SQLAlchemy session.
        account_id: The account to withdraw from.
        amount_cents: Withdrawal amount in cents (must be positive multiple of 2000).
        session_id: Optional session ID for audit logging.

    Returns:
        A dict compatible with WithdrawalResponse containing reference_number,
        transaction_type, amount, balance_after, message, and denominations.

    Raises:
        TransactionError: If the amount is not a valid multiple of $20.
        InsufficientFundsError: If available balance is insufficient.
        DailyLimitExceededError: If the withdrawal would exceed the daily limit.
        AccountFrozenError: If the account is frozen or closed.
    """
    if amount_cents <= 0:
        raise TransactionError("Withdrawal amount must be positive")

    if amount_cents % TWENTY_DOLLAR_BILL_CENTS != 0:
        raise TransactionError("Withdrawal amount must be a multiple of $20.00")

    account = await _load_account(session, account_id)

    # Check available balance
    if account.available_balance_cents < amount_cents:
        await log_event(
            session,
            AuditEventType.WITHDRAWAL_DECLINED,
            account_id=account_id,
            session_id=session_id,
            details={"reason": "insufficient_funds", "amount_cents": amount_cents},
        )
        raise InsufficientFundsError(
            f"Insufficient funds. Available balance: {_format_cents(account.available_balance_cents)}"
        )

    # Check daily limit
    daily_limit = settings.daily_withdrawal_limit
    if account.daily_withdrawal_used_cents + amount_cents > daily_limit:
        remaining = daily_limit - account.daily_withdrawal_used_cents
        await log_event(
            session,
            AuditEventType.WITHDRAWAL_DECLINED,
            account_id=account_id,
            session_id=session_id,
            details={"reason": "daily_limit_exceeded", "amount_cents": amount_cents},
        )
        raise DailyLimitExceededError(
            f"Daily withdrawal limit exceeded. Remaining: {_format_cents(max(0, remaining))}"
        )

    # Check cassette availability
    if not await can_dispense(session, amount_cents):
        raise TransactionError("ATM cannot dispense this amount. Insufficient bills available.")

    # Process withdrawal
    account.balance_cents -= amount_cents
    account.available_balance_cents -= amount_cents
    account.daily_withdrawal_used_cents += amount_cents

    ref = generate_reference_number()
    txn = Transaction(
        account_id=account_id,
        transaction_type=TransactionType.WITHDRAWAL,
        amount_cents=amount_cents,
        balance_after_cents=account.balance_cents,
        reference_number=ref,
        description=f"ATM Withdrawal {_format_cents(amount_cents)}",
    )
    session.add(txn)
    await session.flush()

    # Get denomination breakdown from cassette
    denominations = await dispense_bills(session, amount_cents)

    await log_event(
        session,
        AuditEventType.WITHDRAWAL,
        account_id=account_id,
        session_id=session_id,
        details={"amount_cents": amount_cents, "reference": ref},
    )

    return {
        "reference_number": ref,
        "transaction_type": "WITHDRAWAL",
        "amount": _format_cents(amount_cents),
        "balance_after": _format_cents(account.balance_cents),
        "message": f"Withdrawal of {_format_cents(amount_cents)} successful",
        "denominations": denominations,
    }


async def deposit(
    session: AsyncSession,
    account_id: int,
    amount_cents: int,
    deposit_type: str,
    check_number: str | None = None,
    session_id: str | None = None,
) -> dict[str, object]:
    """Process a cash or check deposit.

    Hold policy:
        - Cash deposits <= $200: fully available immediately.
        - Cash deposits > $200: first $200 immediate, remainder held 1 business day.
        - Check deposits: first $200 available next business day, remainder 2 business days.

    Args:
        session: Async SQLAlchemy session.
        account_id: The account to deposit into.
        amount_cents: Deposit amount in cents (must be positive).
        deposit_type: Either "cash" or "check".
        check_number: Required for check deposits.
        session_id: Optional session ID for audit logging.

    Returns:
        A dict compatible with DepositResponse containing reference_number,
        transaction_type, amount, balance_after, message, available_immediately,
        held_amount, and hold_until.

    Raises:
        TransactionError: If the amount is invalid or deposit_type is wrong.
        AccountFrozenError: If the account is frozen or closed.
    """
    if amount_cents <= 0:
        raise TransactionError("Deposit amount must be positive")

    if deposit_type not in ("cash", "check"):
        raise TransactionError("deposit_type must be 'cash' or 'check'")

    if deposit_type == "check" and not check_number:
        raise TransactionError("Check number is required for check deposits")

    account = await _load_account(session, account_id)
    now = _utcnow()

    # Determine hold policy
    hold_until: datetime | None = None
    available_immediately_cents: int
    held_cents: int

    if deposit_type == "cash":
        txn_type = TransactionType.DEPOSIT_CASH
        if amount_cents <= IMMEDIATE_AVAILABILITY_THRESHOLD_CENTS:
            # Full amount available immediately
            available_immediately_cents = amount_cents
            held_cents = 0
        else:
            # First $200 immediate, rest held 1 business day
            available_immediately_cents = IMMEDIATE_AVAILABILITY_THRESHOLD_CENTS
            held_cents = amount_cents - IMMEDIATE_AVAILABILITY_THRESHOLD_CENTS
            hold_until = _next_business_day(now, days=1)
    else:
        # Check deposit
        txn_type = TransactionType.DEPOSIT_CHECK
        if amount_cents <= IMMEDIATE_AVAILABILITY_THRESHOLD_CENTS:
            available_immediately_cents = 0
            held_cents = amount_cents
            hold_until = _next_business_day(now, days=1)
        else:
            # First $200 available next business day, rest 2 business days
            available_immediately_cents = 0
            held_cents = amount_cents
            hold_until = _next_business_day(now, days=2)

    # Update account balances
    account.balance_cents += amount_cents
    account.available_balance_cents += available_immediately_cents

    ref = generate_reference_number()
    description = (
        f"{'Cash' if deposit_type == 'cash' else 'Check'} Deposit {_format_cents(amount_cents)}"
    )
    if check_number:
        description += f" (Check #{check_number})"

    txn = Transaction(
        account_id=account_id,
        transaction_type=txn_type,
        amount_cents=amount_cents,
        balance_after_cents=account.balance_cents,
        reference_number=ref,
        description=description,
        check_number=check_number,
        hold_until=hold_until,
    )
    session.add(txn)
    await session.flush()

    await log_event(
        session,
        AuditEventType.DEPOSIT,
        account_id=account_id,
        session_id=session_id,
        details={
            "amount_cents": amount_cents,
            "deposit_type": deposit_type,
            "reference": ref,
            "held_cents": held_cents,
        },
    )

    return {
        "reference_number": ref,
        "transaction_type": txn_type.value,
        "amount": _format_cents(amount_cents),
        "balance_after": _format_cents(account.balance_cents),
        "message": f"Deposit of {_format_cents(amount_cents)} successful",
        "available_immediately": _format_cents(available_immediately_cents),
        "held_amount": _format_cents(held_cents),
        "hold_until": hold_until,
    }


async def transfer(
    session: AsyncSession,
    source_account_id: int,
    dest_account_number: str,
    amount_cents: int,
    session_id: str | None = None,
) -> dict[str, object]:
    """Transfer funds between accounts.

    Supports transfers to the user's own accounts and to external accounts
    (looked up by account number). Enforces daily transfer limits.

    Args:
        session: Async SQLAlchemy session.
        source_account_id: The account to transfer from.
        dest_account_number: The destination account number.
        amount_cents: Transfer amount in cents (must be positive).
        session_id: Optional session ID for audit logging.

    Returns:
        A dict compatible with TransferResponse containing reference_number,
        transaction_type, amount, balance_after, message, source_account,
        and destination_account.

    Raises:
        TransactionError: If the transfer is invalid (same account, account not found).
        InsufficientFundsError: If the source account has insufficient funds.
        DailyLimitExceededError: If the transfer would exceed the daily limit.
        AccountFrozenError: If either account is frozen or closed.
    """
    if amount_cents <= 0:
        raise TransactionError("Transfer amount must be positive")

    # Load source account
    source = await _load_account(session, source_account_id)

    # Load destination account by account number
    dest_stmt = select(Account).where(Account.account_number == dest_account_number)
    dest_result = await session.execute(dest_stmt)
    dest = dest_result.scalars().first()

    if dest is None:
        await log_event(
            session,
            AuditEventType.TRANSFER_DECLINED,
            account_id=source_account_id,
            session_id=session_id,
            details={"reason": "destination_not_found", "dest_account": dest_account_number},
        )
        raise TransactionError("Destination account not found")

    # Prevent self-transfer
    if source.id == dest.id:
        raise TransactionError("Cannot transfer to the same account")

    # Check destination status
    if dest.status != AccountStatus.ACTIVE:
        raise TransactionError("Destination account is not active")

    # Check sufficient funds
    if source.available_balance_cents < amount_cents:
        await log_event(
            session,
            AuditEventType.TRANSFER_DECLINED,
            account_id=source_account_id,
            session_id=session_id,
            details={"reason": "insufficient_funds", "amount_cents": amount_cents},
        )
        raise InsufficientFundsError(
            f"Insufficient funds. Available balance: "
            f"{_format_cents(source.available_balance_cents)}"
        )

    # Check daily transfer limit
    daily_limit = settings.daily_transfer_limit
    if source.daily_transfer_used_cents + amount_cents > daily_limit:
        remaining = daily_limit - source.daily_transfer_used_cents
        await log_event(
            session,
            AuditEventType.TRANSFER_DECLINED,
            account_id=source_account_id,
            session_id=session_id,
            details={"reason": "daily_limit_exceeded", "amount_cents": amount_cents},
        )
        raise DailyLimitExceededError(
            f"Daily transfer limit exceeded. Remaining: {_format_cents(max(0, remaining))}"
        )

    # Process transfer
    source.balance_cents -= amount_cents
    source.available_balance_cents -= amount_cents
    source.daily_transfer_used_cents += amount_cents

    dest.balance_cents += amount_cents
    dest.available_balance_cents += amount_cents

    ref = generate_reference_number()

    # Create TRANSFER_OUT transaction on source
    txn_out = Transaction(
        account_id=source.id,
        transaction_type=TransactionType.TRANSFER_OUT,
        amount_cents=amount_cents,
        balance_after_cents=source.balance_cents,
        reference_number=ref,
        description=f"Transfer to {mask_account_number(dest.account_number)}",
        related_account_id=dest.id,
    )
    session.add(txn_out)

    # Create TRANSFER_IN transaction on destination
    ref_in = generate_reference_number()
    txn_in = Transaction(
        account_id=dest.id,
        transaction_type=TransactionType.TRANSFER_IN,
        amount_cents=amount_cents,
        balance_after_cents=dest.balance_cents,
        reference_number=ref_in,
        description=f"Transfer from {mask_account_number(source.account_number)}",
        related_account_id=source.id,
    )
    session.add(txn_in)
    await session.flush()

    await log_event(
        session,
        AuditEventType.TRANSFER,
        account_id=source_account_id,
        session_id=session_id,
        details={
            "amount_cents": amount_cents,
            "source_account": source.account_number,
            "dest_account": dest.account_number,
            "reference": ref,
        },
    )

    return {
        "reference_number": ref,
        "transaction_type": "TRANSFER_OUT",
        "amount": _format_cents(amount_cents),
        "balance_after": _format_cents(source.balance_cents),
        "message": f"Transfer of {_format_cents(amount_cents)} successful",
        "source_account": mask_account_number(source.account_number),
        "destination_account": mask_account_number(dest.account_number),
    }
