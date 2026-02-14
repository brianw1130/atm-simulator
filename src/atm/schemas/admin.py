"""Pydantic schemas for admin CRUD operations."""

from datetime import date

from pydantic import BaseModel, EmailStr, Field, field_validator


class CustomerCreateRequest(BaseModel):
    """Request schema for creating a new customer.

    Attributes:
        first_name: Customer's first name.
        last_name: Customer's last name.
        date_of_birth: Customer's date of birth.
        email: Customer's email address (must be unique).
        phone: Customer's phone number (optional).
    """

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date
    email: EmailStr
    phone: str | None = Field(default=None, max_length=20)


class CustomerUpdateRequest(BaseModel):
    """Request schema for updating an existing customer.

    All fields are optional; only provided fields are updated.

    Attributes:
        first_name: Customer's first name.
        last_name: Customer's last name.
        date_of_birth: Customer's date of birth.
        email: Customer's email address (must be unique).
        phone: Customer's phone number.
    """

    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    date_of_birth: date | None = None
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=20)


class AccountCreateRequest(BaseModel):
    """Request schema for creating a new account.

    Attributes:
        account_type: Type of account (CHECKING or SAVINGS).
        initial_balance_cents: Starting balance in cents (>= 0).
    """

    account_type: str = Field(..., pattern="^(CHECKING|SAVINGS)$")
    initial_balance_cents: int = Field(default=0, ge=0)


class AccountUpdateRequest(BaseModel):
    """Request schema for updating account limits.

    Attributes:
        daily_withdrawal_limit_cents: Daily withdrawal limit in cents.
        daily_transfer_limit_cents: Daily transfer limit in cents.
    """

    daily_withdrawal_limit_cents: int | None = Field(default=None, gt=0)
    daily_transfer_limit_cents: int | None = Field(default=None, gt=0)


class PinResetRequest(BaseModel):
    """Request schema for admin PIN reset.

    Attributes:
        new_pin: The new 4-6 digit PIN.
    """

    new_pin: str = Field(..., min_length=4, max_length=6)

    @field_validator("new_pin")
    @classmethod
    def validate_pin_complexity(cls, v: str) -> str:
        """Validate PIN complexity rules.

        Rules:
            - Must contain only digits.
            - No sequential digits (e.g., 1234, 4321).
            - No repeated digits (e.g., 1111, 0000).
        """
        if not v.isdigit():
            msg = "PIN must contain only digits"
            raise ValueError(msg)

        if len(set(v)) == 1:
            msg = "PIN cannot be all the same digit"
            raise ValueError(msg)

        digits = [int(d) for d in v]
        is_ascending = all(digits[i] + 1 == digits[i + 1] for i in range(len(digits) - 1))
        is_descending = all(digits[i] - 1 == digits[i + 1] for i in range(len(digits) - 1))
        if is_ascending or is_descending:
            msg = "PIN cannot be sequential digits"
            raise ValueError(msg)

        return v


class CardResponse(BaseModel):
    """Response schema for ATM card information.

    Attributes:
        id: Card ID.
        card_number: Card number.
        is_active: Whether the card is active.
        failed_attempts: Number of failed PIN attempts.
        is_locked: Whether the card is currently locked.
    """

    id: int
    card_number: str
    is_active: bool
    failed_attempts: int
    is_locked: bool


class AccountDetailResponse(BaseModel):
    """Response schema for account details within customer detail.

    Attributes:
        id: Account ID.
        account_number: Account number.
        account_type: Type of account.
        balance: Formatted balance string.
        available_balance: Formatted available balance string.
        status: Account status.
        cards: List of cards linked to this account.
    """

    id: int
    account_number: str
    account_type: str
    balance: str
    available_balance: str
    status: str
    cards: list[CardResponse]


class CustomerResponse(BaseModel):
    """Response schema for customer list view.

    Attributes:
        id: Customer ID.
        first_name: Customer's first name.
        last_name: Customer's last name.
        email: Customer's email.
        phone: Customer's phone number.
        date_of_birth: Customer's date of birth.
        is_active: Whether the customer is active.
        account_count: Number of accounts.
    """

    id: int
    first_name: str
    last_name: str
    email: str
    phone: str | None
    date_of_birth: str
    is_active: bool
    account_count: int


class CustomerDetailResponse(BaseModel):
    """Response schema for customer detail view.

    Attributes:
        id: Customer ID.
        first_name: Customer's first name.
        last_name: Customer's last name.
        email: Customer's email.
        phone: Customer's phone number.
        date_of_birth: Customer's date of birth.
        is_active: Whether the customer is active.
        account_count: Number of accounts.
        accounts: List of account details with cards.
    """

    id: int
    first_name: str
    last_name: str
    email: str
    phone: str | None
    date_of_birth: str
    is_active: bool
    account_count: int
    accounts: list[AccountDetailResponse]
