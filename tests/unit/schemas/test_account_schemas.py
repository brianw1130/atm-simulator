"""Unit tests for account Pydantic schemas.

Coverage requirement: 100%

Tests AccountSummary, AccountListResponse, BalanceInquiryResponse, MiniStatementEntry
from src/atm/schemas/account.py.
"""

from datetime import UTC, datetime

from src.atm.models.account import AccountStatus, AccountType
from src.atm.schemas.account import (
    AccountListResponse,
    AccountSummary,
    BalanceInquiryResponse,
    MiniStatementEntry,
)


class TestAccountSummary:
    def test_creation_with_valid_data(self):
        summary = AccountSummary(
            id=1,
            account_number="****-****-0001",
            account_type=AccountType.CHECKING,
            balance="$5,250.00",
            available_balance="$5,250.00",
            status=AccountStatus.ACTIVE,
        )
        assert summary.id == 1
        assert summary.account_number == "****-****-0001"
        assert summary.account_type == AccountType.CHECKING
        assert summary.balance == "$5,250.00"
        assert summary.available_balance == "$5,250.00"
        assert summary.status == AccountStatus.ACTIVE

    def test_savings_account_type(self):
        summary = AccountSummary(
            id=2,
            account_number="****-****-0002",
            account_type=AccountType.SAVINGS,
            balance="$12,500.00",
            available_balance="$12,500.00",
            status=AccountStatus.ACTIVE,
        )
        assert summary.account_type == AccountType.SAVINGS

    def test_frozen_status(self):
        summary = AccountSummary(
            id=3,
            account_number="****-****-0001",
            account_type=AccountType.CHECKING,
            balance="$0.00",
            available_balance="$0.00",
            status=AccountStatus.FROZEN,
        )
        assert summary.status == AccountStatus.FROZEN

    def test_closed_status(self):
        summary = AccountSummary(
            id=4,
            account_number="****-****-0001",
            account_type=AccountType.CHECKING,
            balance="$0.00",
            available_balance="$0.00",
            status=AccountStatus.CLOSED,
        )
        assert summary.status == AccountStatus.CLOSED


class TestMiniStatementEntry:
    def test_creation(self):
        now = datetime.now(tz=UTC)
        entry = MiniStatementEntry(
            date=now,
            description="Cash withdrawal",
            amount="-$100.00",
            balance_after="$5,150.00",
        )
        assert entry.date == now
        assert entry.description == "Cash withdrawal"
        assert entry.amount == "-$100.00"
        assert entry.balance_after == "$5,150.00"


class TestBalanceInquiryResponse:
    def test_creation_with_transactions(self):
        now = datetime.now(tz=UTC)
        account = AccountSummary(
            id=1,
            account_number="****-****-0001",
            account_type=AccountType.CHECKING,
            balance="$5,250.00",
            available_balance="$5,250.00",
            status=AccountStatus.ACTIVE,
        )
        entries = [
            MiniStatementEntry(
                date=now,
                description="Withdrawal",
                amount="-$100.00",
                balance_after="$5,150.00",
            ),
        ]
        response = BalanceInquiryResponse(
            account=account,
            recent_transactions=entries,
        )
        assert response.account.account_number == "****-****-0001"
        assert len(response.recent_transactions) == 1

    def test_creation_with_empty_transactions(self):
        account = AccountSummary(
            id=1,
            account_number="****-****-0001",
            account_type=AccountType.CHECKING,
            balance="$0.00",
            available_balance="$0.00",
            status=AccountStatus.ACTIVE,
        )
        response = BalanceInquiryResponse(
            account=account,
            recent_transactions=[],
        )
        assert len(response.recent_transactions) == 0


class TestAccountListResponse:
    def test_creation_with_multiple_accounts(self):
        accounts = [
            AccountSummary(
                id=1,
                account_number="****-****-0001",
                account_type=AccountType.CHECKING,
                balance="$5,250.00",
                available_balance="$5,250.00",
                status=AccountStatus.ACTIVE,
            ),
            AccountSummary(
                id=2,
                account_number="****-****-0002",
                account_type=AccountType.SAVINGS,
                balance="$12,500.00",
                available_balance="$12,500.00",
                status=AccountStatus.ACTIVE,
            ),
        ]
        response = AccountListResponse(accounts=accounts)
        assert len(response.accounts) == 2
        assert response.accounts[0].account_type == AccountType.CHECKING
        assert response.accounts[1].account_type == AccountType.SAVINGS

    def test_creation_with_empty_list(self):
        response = AccountListResponse(accounts=[])
        assert len(response.accounts) == 0
