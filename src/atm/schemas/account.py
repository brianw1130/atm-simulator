"""Pydantic schemas for account operations."""

from datetime import datetime

from pydantic import BaseModel

from src.atm.models.account import AccountStatus, AccountType


class AccountSummary(BaseModel):
    """Summary view of an account for balance inquiries.

    Attributes:
        account_number: Masked account number (last 4 visible).
        account_type: CHECKING or SAVINGS.
        balance: Formatted total balance (e.g., "$1,234.56").
        available_balance: Formatted available balance.
        status: Account status.
    """

    account_number: str
    account_type: AccountType
    balance: str
    available_balance: str
    status: AccountStatus

    model_config = {"from_attributes": True}


class MiniStatementEntry(BaseModel):
    """A single transaction entry in a mini-statement.

    Attributes:
        date: Transaction date and time.
        description: Human-readable description.
        amount: Formatted amount with sign indicator.
        balance_after: Formatted balance after transaction.
    """

    date: datetime
    description: str
    amount: str
    balance_after: str


class BalanceInquiryResponse(BaseModel):
    """Response schema for balance inquiry with mini-statement.

    Attributes:
        account: Account summary information.
        recent_transactions: Last 5 transactions.
    """

    account: AccountSummary
    recent_transactions: list[MiniStatementEntry]


class AccountListResponse(BaseModel):
    """Response schema containing a list of account summaries.

    Attributes:
        accounts: List of account summary objects.
    """

    accounts: list[AccountSummary]
