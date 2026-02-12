"""Pydantic schemas for authentication operations."""

from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    """Request schema for PIN-based authentication.

    Attributes:
        card_number: The ATM card number.
        pin: The 4-6 digit PIN.
    """

    card_number: str = Field(..., min_length=1, max_length=20, description="ATM card number")
    pin: str = Field(..., min_length=4, max_length=6, description="4-6 digit PIN")

    @field_validator("pin")
    @classmethod
    def pin_must_be_digits(cls, v: str) -> str:
        """Validate that PIN contains only digits."""
        if not v.isdigit():
            msg = "PIN must contain only digits"
            raise ValueError(msg)
        return v


class LoginResponse(BaseModel):
    """Response schema for successful authentication."""

    session_id: str
    account_number: str
    customer_name: str
    message: str = "Authentication successful"


class PinChangeRequest(BaseModel):
    """Request schema for changing a PIN.

    Attributes:
        current_pin: The current PIN for verification.
        new_pin: The desired new PIN.
        confirm_pin: Confirmation of the new PIN.
    """

    current_pin: str = Field(..., min_length=4, max_length=6)
    new_pin: str = Field(..., min_length=4, max_length=6)
    confirm_pin: str = Field(..., min_length=4, max_length=6)

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

        # Check for all same digits
        if len(set(v)) == 1:
            msg = "PIN cannot be all the same digit"
            raise ValueError(msg)

        # Check for sequential digits (ascending or descending)
        digits = [int(d) for d in v]
        is_ascending = all(digits[i] + 1 == digits[i + 1] for i in range(len(digits) - 1))
        is_descending = all(digits[i] - 1 == digits[i + 1] for i in range(len(digits) - 1))
        if is_ascending or is_descending:
            msg = "PIN cannot be sequential digits"
            raise ValueError(msg)

        return v

    @field_validator("confirm_pin")
    @classmethod
    def pins_must_match(cls, v: str, info: object) -> str:
        """Validate that new_pin and confirm_pin match."""
        # Access other field values through info.data
        if hasattr(info, "data") and "new_pin" in info.data and v != info.data["new_pin"]:  # type: ignore[union-attr]
            msg = "PINs do not match"
            raise ValueError(msg)
        return v


class PinChangeResponse(BaseModel):
    """Response schema for successful PIN change."""

    message: str = "PIN changed successfully"
