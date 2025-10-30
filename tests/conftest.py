import os
import asyncio
import typing as t

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.main import app
from app.core.deps import get_db
from app.db.base import Base
from app.core.config import settings


def _build_test_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    # Fallback: derive from main DATABASE_URL by appending _test to db name
    # Assumes standard postgres url shape
    raw = str(settings.DATABASE_URL)
    if "/" in raw.rsplit("/", 1)[-1]:
        return raw
    head, tail = raw.rsplit("/", 1)
    return f"{head}/{tail}_test"


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def engine() -> t.AsyncGenerator[AsyncEngine, None]:
    database_url = _build_test_database_url()
    eng = create_async_engine(database_url, echo=False, pool_pre_ping=True)
    # Create schema
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield eng
    finally:
        # Drop schema after session
        async with eng.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await eng.dispose()


@pytest.fixture(scope="function")
async def db_session(engine: AsyncEngine) -> t.AsyncGenerator[AsyncSession, None]:
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
    async with SessionLocal() as session:
        yield session


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> t.AsyncGenerator[AsyncClient, None]:
    # Override DB dependency to use test session
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()


async def _signup_and_login(ac: AsyncClient, email: str, username: str, password: str) -> dict:
    # Signup
    s = await ac.post(
        "/api/v1/auth/signup",
        json={"email": email, "username": username, "password": password},
    )
    assert s.status_code in (200, 201), s.text
    # Login
    l = await ac.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert l.status_code == 200, l.text
    return l.json()


@pytest.fixture()
async def auth_tokens(client: AsyncClient) -> dict:
    return await _signup_and_login(
        client,
        email="user1@example.com",
        username="user1",
        password="StrongPassw0rd!",
    )


