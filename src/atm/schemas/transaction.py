"""Pydantic schemas for transaction operations."""

from pydantic import BaseModel, Field, field_validator


class WithdrawalRequest(BaseModel):
    """Request schema for cash withdrawal.

    Attributes:
        amount_cents: Withdrawal amount in cents. Must be a positive multiple of 2000 ($20).
    """

    amount_cents: int = Field(..., gt=0, description="Amount in cents (must be multiple of 2000)")

    @field_validator("amount_cents")
    @classmethod
    def must_be_multiple_of_twenty_dollars(cls, v: int) -> int:
        """Validate that amount is a multiple of $20 (2000 cents)."""
        if v % 2000 != 0:
            msg = "Withdrawal amount must be a multiple of $20.00"
            raise ValueError(msg)
        return v


class DepositRequest(BaseModel):
    """Request schema for cash or check deposit.

    Attributes:
        amount_cents: Deposit amount in cents. Must be positive.
        deposit_type: Either 'cash' or 'check'.
        check_number: Required for check deposits.
    """

    amount_cents: int = Field(..., gt=0, description="Amount in cents")
    deposit_type: str = Field(..., pattern="^(cash|check)$", description="'cash' or 'check'")
    check_number: str | None = Field(
        None, max_length=20, description="Check number (required for check deposits)"
    )

    @field_validator("check_number")
    @classmethod
    def check_number_required_for_checks(cls, v: str | None, info: object) -> str | None:
        """Validate that check_number is provided for check deposits."""
        if (
            hasattr(info, "data")
            and info.data.get("deposit_type") == "check"  # type: ignore[union-attr]
            and not v
        ):
            msg = "Check number is required for check deposits"
            raise ValueError(msg)
        return v


class TransferRequest(BaseModel):
    """Request schema for fund transfer.

    Attributes:
        destination_account_number: The target account number.
        amount_cents: Transfer amount in cents. Must be positive.
    """

    destination_account_number: str = Field(
        ..., min_length=1, max_length=20, description="Destination account number"
    )
    amount_cents: int = Field(..., gt=0, description="Amount in cents")


class TransactionResponse(BaseModel):
    """Response schema for completed transactions.

    Attributes:
        reference_number: Unique transaction reference.
        transaction_type: Type of transaction performed.
        amount: Formatted dollar amount.
        balance_after: Formatted balance after transaction.
        message: Human-readable confirmation message.
    """

    reference_number: str
    transaction_type: str
    amount: str
    balance_after: str
    message: str


class StatementRequest(BaseModel):
    """Request schema for generating an account statement.

    Attributes:
        days: Number of days to include (7, 30, 90, or custom via start/end dates).
    """

    days: int = Field(default=30, ge=1, le=365, description="Number of days for statement")


class StatementResponse(BaseModel):
    """Response schema for a generated statement.

    Attributes:
        file_path: Path to the generated PDF file.
        period: Human-readable period description.
        transaction_count: Number of transactions in the statement.
        opening_balance: Formatted opening balance.
        closing_balance: Formatted closing balance.
    """

    file_path: str
    period: str
    transaction_count: int
    opening_balance: str
    closing_balance: str
