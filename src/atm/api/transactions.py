"""Transaction API endpoints (withdrawals, deposits, transfers).

Owner: Backend Engineer
Depends on: transaction_service, transaction schemas

Routes:
    POST /withdraw — Cash withdrawal
    POST /deposit — Cash or check deposit
    POST /transfer — Fund transfer
"""

from fastapi import APIRouter, Header, HTTPException, status
from typing import Annotated

from src.atm.api import CurrentSession, DbSession
from src.atm.schemas.transaction import (
    DepositRequest,
    DepositResponse,
    ErrorResponse,
    TransferRequest,
    TransferResponse,
    WithdrawalRequest,
    WithdrawalResponse,
)
from src.atm.services.transaction_service import (
    AccountFrozenError,
    DailyLimitExceededError,
    InsufficientFundsError,
    TransactionError,
    deposit,
    transfer,
    withdraw,
)

router = APIRouter()


@router.post(
    "/withdraw",
    response_model=WithdrawalResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
    },
)
async def withdraw_endpoint(
    body: WithdrawalRequest,
    db: DbSession,
    session_info: CurrentSession,
    x_session_id: Annotated[str, Header()],
) -> WithdrawalResponse:
    """Process a cash withdrawal.

    Args:
        body: Withdrawal request with amount_cents.
        db: Database session dependency.
        session_info: Validated session data from dependency.
        x_session_id: Session token for audit logging.

    Returns:
        Withdrawal receipt with denomination breakdown.
    """
    try:
        result = await withdraw(
            db,
            session_info["account_id"],
            body.amount_cents,
            session_id=x_session_id,
        )
    except AccountFrozenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except InsufficientFundsError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except DailyLimitExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except TransactionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return WithdrawalResponse(**result)


@router.post(
    "/deposit",
    response_model=DepositResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
    },
)
async def deposit_endpoint(
    body: DepositRequest,
    db: DbSession,
    session_info: CurrentSession,
    x_session_id: Annotated[str, Header()],
) -> DepositResponse:
    """Process a cash or check deposit.

    Args:
        body: Deposit request with amount, type, and optional check number.
        db: Database session dependency.
        session_info: Validated session data from dependency.
        x_session_id: Session token for audit logging.

    Returns:
        Deposit receipt with hold information.
    """
    try:
        result = await deposit(
            db,
            session_info["account_id"],
            body.amount_cents,
            body.deposit_type,
            check_number=body.check_number,
            session_id=x_session_id,
        )
    except AccountFrozenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except TransactionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return DepositResponse(**result)


@router.post(
    "/transfer",
    response_model=TransferResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
async def transfer_endpoint(
    body: TransferRequest,
    db: DbSession,
    session_info: CurrentSession,
    x_session_id: Annotated[str, Header()],
) -> TransferResponse:
    """Transfer funds to another account.

    Args:
        body: Transfer request with destination account and amount.
        db: Database session dependency.
        session_info: Validated session data from dependency.
        x_session_id: Session token for audit logging.

    Returns:
        Transfer receipt with source and destination details.
    """
    try:
        result = await transfer(
            db,
            session_info["account_id"],
            body.destination_account_number,
            body.amount_cents,
            session_id=x_session_id,
        )
    except AccountFrozenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except InsufficientFundsError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except DailyLimitExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except TransactionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return TransferResponse(**result)
