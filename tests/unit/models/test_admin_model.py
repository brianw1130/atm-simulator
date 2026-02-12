"""Unit tests for AdminUser model.

Coverage requirement: 100%

Tests: model creation with all fields, default values (role, is_active).
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.atm.models.admin import AdminUser

pytestmark = pytest.mark.asyncio


class TestAdminUserModel:
    async def test_create_with_all_fields(self, db_session: AsyncSession) -> None:
        """AdminUser can be created with explicit values for all fields."""
        admin = AdminUser(
            username="testadmin",
            password_hash="$2b$12$fakehashfortest",
            role="superadmin",
            is_active=False,
        )
        db_session.add(admin)
        await db_session.flush()

        assert admin.id is not None
        assert admin.username == "testadmin"
        assert admin.password_hash == "$2b$12$fakehashfortest"
        assert admin.role == "superadmin"
        assert admin.is_active is False
        assert admin.created_at is not None

    async def test_default_role_is_admin(self, db_session: AsyncSession) -> None:
        """role defaults to 'admin' when not specified."""
        admin = AdminUser(
            username="defaultrole",
            password_hash="$2b$12$anotherfakehash",
        )
        db_session.add(admin)
        await db_session.flush()

        assert admin.role == "admin"

    async def test_default_is_active_is_true(self, db_session: AsyncSession) -> None:
        """is_active defaults to True when not specified."""
        admin = AdminUser(
            username="activedefault",
            password_hash="$2b$12$yetanotherhash",
        )
        db_session.add(admin)
        await db_session.flush()

        assert admin.is_active is True

    async def test_tablename(self) -> None:
        """The table name is 'admin_users'."""
        assert AdminUser.__tablename__ == "admin_users"

    async def test_username_is_stored(self, db_session: AsyncSession) -> None:
        """Username is persisted correctly."""
        admin = AdminUser(
            username="uniqueadmin",
            password_hash="$2b$12$hash",
        )
        db_session.add(admin)
        await db_session.flush()

        from sqlalchemy import select

        stmt = select(AdminUser).where(AdminUser.username == "uniqueadmin")
        result = await db_session.execute(stmt)
        fetched = result.scalars().first()
        assert fetched is not None
        assert fetched.username == "uniqueadmin"
