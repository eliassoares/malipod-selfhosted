from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import Settings, clear_settings_cache, get_settings
from app.db.session import (
    close_database_connections,
    get_db_session,
    initialize_database,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture(autouse=True)
def isolate_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> Iterator[None]:
    database_path = tmp_path / "test.sqlite3"
    monkeypatch.setenv("APP_NAME", "Malipod Test")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+asyncpg://ignored:ignored@localhost:5432/ignored"
    )
    monkeypatch.setenv("TEST_DATABASE_URL", f"sqlite+aiosqlite:///{database_path}")
    monkeypatch.setenv("SECRET_KEY", "a" * 32)
    monkeypatch.setenv("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("ARCHIVE_DIR", str(tmp_path / "archive"))
    monkeypatch.setenv("ARCHIVE_WORKERS", "1")
    monkeypatch.setenv("ARCHIVE_SYNC_INTERVAL_MINUTES", "9999")
    clear_settings_cache()
    yield
    clear_settings_cache()
    loop = asyncio.new_event_loop()
    loop.run_until_complete(close_database_connections())
    loop.close()


@pytest.fixture
def client() -> Iterator[TestClient]:
    from app.main import create_app

    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture
def settings() -> Settings:
    return get_settings()


@pytest_asyncio.fixture
async def db_session(settings: Settings) -> AsyncIterator[AsyncSession]:
    await initialize_database(settings)
    async for session in get_db_session(settings):
        yield session
