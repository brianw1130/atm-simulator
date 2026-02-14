"""Pydantic request and response schemas for API validation."""

from src.atm.schemas.account import (
    AccountListResponse,
    AccountSummary,
    BalanceInquiryResponse,
    MiniStatementEntry,
)
from src.atm.schemas.admin import (
    AccountCreateRequest,
    AccountDetailResponse,
    AccountUpdateRequest,
    CardResponse,
    CustomerCreateRequest,
    CustomerDetailResponse,
    CustomerResponse,
    CustomerUpdateRequest,
    PinResetRequest,
)
from src.atm.schemas.auth import (
    LoginRequest,
    LoginResponse,
    PinChangeRequest,
    PinChangeResponse,
)
from src.atm.schemas.transaction import (
    DenominationBreakdown,
    DepositRequest,
    DepositResponse,
    ErrorResponse,
    StatementRequest,
    StatementResponse,
    TransactionResponse,
    TransferRequest,
    TransferResponse,
    WithdrawalRequest,
    WithdrawalResponse,
)

__all__ = [
    "AccountCreateRequest",
    "AccountDetailResponse",
    "AccountListResponse",
    "AccountSummary",
    "AccountUpdateRequest",
    "BalanceInquiryResponse",
    "CardResponse",
    "CustomerCreateRequest",
    "CustomerDetailResponse",
    "CustomerResponse",
    "CustomerUpdateRequest",
    "DenominationBreakdown",
    "DepositRequest",
    "DepositResponse",
    "ErrorResponse",
    "LoginRequest",
    "LoginResponse",
    "MiniStatementEntry",
    "PinChangeRequest",
    "PinChangeResponse",
    "PinResetRequest",
    "StatementRequest",
    "StatementResponse",
    "TransactionResponse",
    "TransferRequest",
    "TransferResponse",
    "WithdrawalRequest",
    "WithdrawalResponse",
]
