from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db.base import Base

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from app.core.config import Settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine(settings: Settings) -> AsyncEngine:
    global _engine, _session_factory
    if _engine is None:
        _engine = create_async_engine(settings.effective_database_url, future=True)
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def get_session_factory(settings: Settings) -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        get_engine(settings)
    if _session_factory is None:
        raise RuntimeError("database session factory could not be initialized")
    return _session_factory


async def get_db_session(settings: Settings) -> AsyncIterator[AsyncSession]:
    session_factory = get_session_factory(settings)
    async with session_factory() as session:
        yield session


async def initialize_database(settings: Settings) -> None:
    import_module("app.db.models")
    engine = get_engine(settings)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def ping_database(settings: Settings) -> None:
    engine = get_engine(settings)
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))


async def close_database_connections() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None
