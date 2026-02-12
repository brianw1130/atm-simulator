"""Unit tests for audit_service.

Coverage requirement: 100%

Tests:
    - log_event creates an AuditLog entry with correct fields
    - log_event works with minimal args (event_type only)
    - log_event works with all optional args
    - The returned AuditLog has an assigned ID after flush
"""

import pytest
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
