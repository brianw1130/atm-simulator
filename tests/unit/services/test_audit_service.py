"""Unit tests for audit_service.

Coverage requirement: 100%

Tests:
    - log_event creates an AuditLog entry with correct fields
    - log_event works with minimal args (event_type only)
    - log_event works with all optional args
    - The returned AuditLog has an assigned ID after flush
    - Detailed JSON persistence and querying by various fields
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.atm.models.audit import AuditEventType, AuditLog
from src.atm.services.audit_service import log_event

pytestmark = pytest.mark.asyncio


class TestLogEvent:
    async def test_creates_audit_entry_with_event_type(self, db_session: AsyncSession):
        entry = await log_event(db_session, AuditEventType.LOGIN_SUCCESS)
        assert entry.event_type == AuditEventType.LOGIN_SUCCESS
        assert entry.id is not None

    async def test_creates_entry_with_all_fields(self, db_session: AsyncSession):
        entry = await log_event(
            db_session,
            AuditEventType.WITHDRAWAL,
            account_id=42,
            ip_address="192.168.1.1",
            session_id="session-abc",
            details={"amount_cents": 10000},
        )
        assert entry.event_type == AuditEventType.WITHDRAWAL
        assert entry.account_id == 42
        assert entry.ip_address == "192.168.1.1"
        assert entry.session_id == "session-abc"
        assert entry.details == {"amount_cents": 10000}

    async def test_optional_fields_default_to_none(self, db_session: AsyncSession):
        entry = await log_event(db_session, AuditEventType.LOGOUT)
        assert entry.account_id is None
        assert entry.ip_address is None
        assert entry.session_id is None
        assert entry.details is None

    async def test_returns_audit_log_instance(self, db_session: AsyncSession):
        entry = await log_event(db_session, AuditEventType.DEPOSIT)
        assert isinstance(entry, AuditLog)

    async def test_entry_is_persisted_with_id(self, db_session: AsyncSession):
        entry = await log_event(
            db_session,
            AuditEventType.PIN_CHANGED,
            account_id=1,
        )
        assert entry.id is not None
        assert entry.id > 0

    async def test_multiple_entries_get_different_ids(self, db_session: AsyncSession):
        e1 = await log_event(db_session, AuditEventType.LOGIN_SUCCESS)
        e2 = await log_event(db_session, AuditEventType.LOGIN_FAILED)
        assert e1.id != e2.id

    async def test_all_event_types(self, db_session: AsyncSession):
        for event_type in AuditEventType:
            entry = await log_event(db_session, event_type)
            assert entry.event_type == event_type


class TestLogEventCreatedAt:
    async def test_created_at_is_set_automatically(self, db_session: AsyncSession):
        entry = await log_event(db_session, AuditEventType.LOGIN_SUCCESS)
        assert entry.created_at is not None

    async def test_created_at_ordering(self, db_session: AsyncSession):
        e1 = await log_event(db_session, AuditEventType.LOGIN_SUCCESS)
        e2 = await log_event(db_session, AuditEventType.WITHDRAWAL)
        assert e2.created_at >= e1.created_at


class TestLogEventDetails:
    async def test_nested_json_details(self, db_session: AsyncSession):
        nested = {
            "amount_cents": 10000,
            "denominations": {"twenties": 5, "total": 5},
            "metadata": {"source": "ATM-001"},
        }
        entry = await log_event(
            db_session, AuditEventType.WITHDRAWAL, details=nested
        )
        assert entry.details == nested
        assert entry.details["denominations"]["twenties"] == 5

    async def test_list_in_details(self, db_session: AsyncSession):
        details = {"accounts": [1, 2, 3], "action": "multi_check"}
        entry = await log_event(
            db_session, AuditEventType.BALANCE_INQUIRY, details=details
        )
        assert entry.details["accounts"] == [1, 2, 3]

    async def test_empty_dict_details(self, db_session: AsyncSession):
        entry = await log_event(
            db_session, AuditEventType.LOGOUT, details={}
        )
        assert entry.details == {}


class TestLogEventQuerying:
    async def test_query_by_event_type(self, db_session: AsyncSession):
        await log_event(db_session, AuditEventType.LOGIN_SUCCESS)
        await log_event(db_session, AuditEventType.LOGIN_FAILED)
        await log_event(db_session, AuditEventType.LOGIN_SUCCESS)

        stmt = select(AuditLog).where(
            AuditLog.event_type == AuditEventType.LOGIN_SUCCESS
        )
        results = list((await db_session.execute(stmt)).scalars().all())
        assert len(results) == 2

    async def test_query_by_account_id(self, db_session: AsyncSession):
        await log_event(db_session, AuditEventType.WITHDRAWAL, account_id=10)
        await log_event(db_session, AuditEventType.DEPOSIT, account_id=10)
        await log_event(db_session, AuditEventType.WITHDRAWAL, account_id=20)

        stmt = select(AuditLog).where(AuditLog.account_id == 10)
        results = list((await db_session.execute(stmt)).scalars().all())
        assert len(results) == 2

    async def test_query_by_session_id(self, db_session: AsyncSession):
        await log_event(
            db_session, AuditEventType.LOGIN_SUCCESS, session_id="sess-001"
        )
        await log_event(
            db_session, AuditEventType.WITHDRAWAL, session_id="sess-001"
        )
        await log_event(
            db_session, AuditEventType.LOGOUT, session_id="sess-001"
        )
        await log_event(
            db_session, AuditEventType.LOGIN_SUCCESS, session_id="sess-002"
        )

        stmt = select(AuditLog).where(AuditLog.session_id == "sess-001")
        results = list((await db_session.execute(stmt)).scalars().all())
        assert len(results) == 3

    async def test_query_no_results(self, db_session: AsyncSession):
        await log_event(db_session, AuditEventType.LOGIN_SUCCESS)

        stmt = select(AuditLog).where(
            AuditLog.event_type == AuditEventType.ACCOUNT_FROZEN
        )
        results = list((await db_session.execute(stmt)).scalars().all())
        assert len(results) == 0

    async def test_entries_ordered_by_id(self, db_session: AsyncSession):
        e1 = await log_event(db_session, AuditEventType.LOGIN_SUCCESS)
        e2 = await log_event(db_session, AuditEventType.WITHDRAWAL)
        e3 = await log_event(db_session, AuditEventType.LOGOUT)

        stmt = select(AuditLog).order_by(AuditLog.id.asc())
        results = list((await db_session.execute(stmt)).scalars().all())
        assert len(results) == 3
        assert results[0].id == e1.id
        assert results[1].id == e2.id
        assert results[2].id == e3.id


class TestLogEventSecurityScenarios:
    async def test_login_failure_with_ip(self, db_session: AsyncSession):
        entry = await log_event(
            db_session,
            AuditEventType.LOGIN_FAILED,
            account_id=5,
            ip_address="10.0.0.1",
            details={"reason": "invalid_pin", "attempt": 2},
        )
        assert entry.event_type == AuditEventType.LOGIN_FAILED
        assert entry.details["reason"] == "invalid_pin"
        assert entry.details["attempt"] == 2

    async def test_account_lockout_event(self, db_session: AsyncSession):
        entry = await log_event(
            db_session,
            AuditEventType.ACCOUNT_LOCKED,
            account_id=5,
            details={"locked_duration_seconds": 1800},
        )
        assert entry.event_type == AuditEventType.ACCOUNT_LOCKED
        assert entry.details["locked_duration_seconds"] == 1800

    async def test_pin_change_failure(self, db_session: AsyncSession):
        entry = await log_event(
            db_session,
            AuditEventType.PIN_CHANGE_FAILED,
            account_id=3,
            details={"reason": "sequential_digits"},
        )
        assert entry.event_type == AuditEventType.PIN_CHANGE_FAILED
        assert entry.details["reason"] == "sequential_digits"

    async def test_maintenance_mode_events(self, db_session: AsyncSession):
        e1 = await log_event(
            db_session,
            AuditEventType.MAINTENANCE_ENABLED,
            details={"enabled_by": "admin"},
        )
        e2 = await log_event(
            db_session,
            AuditEventType.MAINTENANCE_DISABLED,
            details={"disabled_by": "admin"},
        )
        assert e1.event_type == AuditEventType.MAINTENANCE_ENABLED
        assert e2.event_type == AuditEventType.MAINTENANCE_DISABLED

    async def test_validation_failure_event(self, db_session: AsyncSession):
        entry = await log_event(
            db_session,
            AuditEventType.VALIDATION_FAILURE,
            ip_address="192.168.1.100",
            details={"field": "amount_cents", "value": -500},
        )
        assert entry.event_type == AuditEventType.VALIDATION_FAILURE
        assert entry.details["value"] == -500

    async def test_withdrawal_declined_event(self, db_session: AsyncSession):
        entry = await log_event(
            db_session,
            AuditEventType.WITHDRAWAL_DECLINED,
            account_id=7,
            session_id="sess-decline-001",
            details={"reason": "daily_limit_exceeded", "amount_cents": 60000},
        )
        assert entry.event_type == AuditEventType.WITHDRAWAL_DECLINED
        assert entry.account_id == 7
        assert entry.session_id == "sess-decline-001"

    async def test_transfer_declined_event(self, db_session: AsyncSession):
        entry = await log_event(
            db_session,
            AuditEventType.TRANSFER_DECLINED,
            account_id=8,
            details={"reason": "destination_not_found", "dest": "9999-9999"},
        )
        assert entry.event_type == AuditEventType.TRANSFER_DECLINED
        assert entry.details["reason"] == "destination_not_found"
