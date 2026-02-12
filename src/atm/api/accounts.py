"""Account management API endpoints.

Owner: Backend Engineer
Depends on: account_service, account schemas

Routes:
    GET / — List accounts for authenticated customer
    GET /{account_id}/balance — Balance inquiry with mini-statement
"""

from fastapi import APIRouter, HTTPException, status

from src.atm.api import CurrentSession, DbSession
from src.atm.schemas.account import (
    AccountListResponse,
    AccountSummary,
    BalanceInquiryResponse,
)
from src.atm.schemas.transaction import ErrorResponse
from src.atm.services.account_service import (
    AccountError,
    get_account_balance,
    get_customer_accounts,
)
from src.atm.utils.formatting import mask_account_number

router = APIRouter()


@router.get(
    "/",
    response_model=AccountListResponse,
)
async def list_accounts(
    db: DbSession,
    session_info: CurrentSession,
) -> AccountListResponse:
    """List all accounts for the authenticated customer.

    Args:
        db: Database session dependency.
        session_info: Validated session data from dependency.

    Returns:
        List of account summaries.
    """
    accounts = await get_customer_accounts(db, session_info["customer_id"])
    summaries = [
        AccountSummary(
            account_number=mask_account_number(acct.account_number),
            account_type=acct.account_type,
            balance=acct.balance_dollars,
            available_balance=acct.available_balance_dollars,
            status=acct.status,
        )
        for acct in accounts
    ]
    return AccountListResponse(accounts=summaries)


@router.get(
    "/{account_id}/balance",
    response_model=BalanceInquiryResponse,
    responses={404: {"model": ErrorResponse}},
)
async def balance_inquiry(
    account_id: int,
    db: DbSession,
    session_info: CurrentSession,
) -> BalanceInquiryResponse:
    """Get balance information and mini-statement for a specific account.

    Args:
        account_id: The account ID to query.
        db: Database session dependency.
        session_info: Validated session data from dependency.

    Returns:
        Balance details and last 5 transactions.
    """
    try:
        result = await get_account_balance(db, account_id)
    except AccountError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    return BalanceInquiryResponse(**result)
