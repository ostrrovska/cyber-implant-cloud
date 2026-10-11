# Lab2
from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator, Awaitable, Callable

import asyncpg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_session
from app.main import app
from app.models.user import UserRole
from app.services import user_service

_TEST_DB_NAME = "cyberimplant_test"


def _test_database_url() -> str:
    override = os.getenv("TEST_DATABASE_URL")
    if override:
        return override
    url = make_url(get_settings().database_url).set(database=_TEST_DB_NAME)
    return url.render_as_string(hide_password=False)


async def _ensure_database() -> None:
    url = make_url(_test_database_url())
    admin = await asyncpg.connect(
        host=url.host,
        port=url.port,
        user=url.username,
        password=url.password,
        database="postgres",
    )
    try:
        exists = await admin.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", url.database)
        if not exists:
            await admin.execute(f'CREATE DATABASE "{url.database}"')
    finally:
        await admin.close()


@pytest.fixture(scope="session", autouse=True)
def _create_test_database() -> None:
    asyncio.run(_ensure_database())


@pytest_asyncio.fixture
async def session() -> AsyncIterator:
    engine = create_async_engine(_test_database_url(), poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        yield s
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(session) -> AsyncIterator[AsyncClient]:
    async def _override() -> AsyncIterator:
        yield session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


AuthFactory = Callable[..., Awaitable[dict[str, str]]]


@pytest_asyncio.fixture
async def make_user(client: AsyncClient, session) -> AuthFactory:
    """Create a user (admin via service, regular via the public API) and return auth headers."""

    async def _make(
        email: str, password: str = "password123", role: UserRole = UserRole.USER
    ) -> dict[str, str]:
        if role == UserRole.ADMIN:
            await user_service.register_user(session, email, password, role=UserRole.ADMIN)
        else:
            await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _make
