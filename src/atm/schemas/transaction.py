"""Pydantic schemas for transaction operations."""

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator, model_validator


class WithdrawalRequest(BaseModel):
    """Request schema for cash withdrawal.

    Attributes:
        amount_cents: Withdrawal amount in cents. Must be a positive multiple of 2000 ($20).
    """

    amount_cents: int = Field(
        ..., gt=0, description="Amount in cents (must be multiple of 2000)"
    )

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
    deposit_type: str = Field(
        ..., pattern="^(cash|check)$", description="'cash' or 'check'"
    )
    check_number: str | None = Field(
        None, max_length=20, description="Check number (required for check deposits)"
    )

    @field_validator("check_number")
    @classmethod
    def check_number_required_for_checks(
        cls, v: str | None, info: object
    ) -> str | None:
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


class ErrorResponse(BaseModel):
    """Standard error response schema.

    Attributes:
        error: Short error category (e.g., 'insufficient_funds').
        detail: Human-readable error description.
        error_code: Machine-readable error code for client handling.
    """

    error: str = Field(..., description="Short error category")
    detail: str = Field(..., description="Human-readable error description")
    error_code: str = Field(..., description="Machine-readable error code")


class DenominationBreakdown(BaseModel):
    """Breakdown of cash denominations dispensed.

    Attributes:
        twenties: Number of $20 bills.
        total_bills: Total number of bills dispensed.
        total_amount: Formatted total dollar amount.
    """

    twenties: int = Field(..., ge=0, description="Number of $20 bills")
    total_bills: int = Field(..., ge=0, description="Total number of bills")
    total_amount: str = Field(..., description="Formatted total dollar amount")


class WithdrawalResponse(TransactionResponse):
    """Response schema for cash withdrawal, including denomination breakdown.

    Attributes:
        denominations: Breakdown of bills dispensed.
    """

    denominations: DenominationBreakdown


class DepositResponse(TransactionResponse):
    """Response schema for deposits, including hold information.

    Attributes:
        available_immediately: Formatted amount available immediately.
        held_amount: Formatted amount placed on hold.
        hold_until: Datetime when held funds become available (None if no hold).
    """

    available_immediately: str = Field(
        ..., description="Formatted amount available immediately"
    )
    held_amount: str = Field(..., description="Formatted amount on hold")
    hold_until: datetime | None = Field(
        None, description="When held funds become available"
    )


class TransferResponse(TransactionResponse):
    """Response schema for fund transfers.

    Attributes:
        source_account: Masked source account number.
        destination_account: Masked destination account number.
    """

    source_account: str = Field(..., description="Masked source account number")
    destination_account: str = Field(
        ..., description="Masked destination account number"
    )


class StatementRequest(BaseModel):
    """Request schema for generating an account statement.

    Supports two modes: specify `days` for a relative period,
    or specify `start_date` and `end_date` for a custom range.
    If both are provided, `start_date`/`end_date` take precedence.

    Attributes:
        days: Number of days to include (7, 30, 90, or custom).
        start_date: Custom range start date (inclusive).
        end_date: Custom range end date (inclusive).
    """

    days: int = Field(
        default=30, ge=1, le=365, description="Number of days for statement"
    )
    start_date: date | None = Field(
        None, description="Custom range start date (inclusive)"
    )
    end_date: date | None = Field(
        None, description="Custom range end date (inclusive)"
    )

    @model_validator(mode="after")
    def validate_date_range(self) -> "StatementRequest":
        """Validate that custom date range is consistent.

        Rules:
            - If one of start_date/end_date is set, both must be set.
            - end_date must not be before start_date.
            - end_date must not be in the future.
        """
        if self.start_date is not None or self.end_date is not None:
            if self.start_date is None or self.end_date is None:
                msg = "Both start_date and end_date must be provided for custom range"
                raise ValueError(msg)
            if self.end_date < self.start_date:
                msg = "end_date must not be before start_date"
                raise ValueError(msg)
            if self.end_date > date.today():
                msg = "end_date must not be in the future"
                raise ValueError(msg)
        return self


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
