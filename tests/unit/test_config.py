from __future__ import annotations

import pytest

from app.core.config import Settings


def test_test_environment_uses_isolated_database() -> None:
    settings = Settings(
        database_url="postgresql+asyncpg://ignored:ignored@localhost:5432/ignored",
        test_database_url="sqlite+aiosqlite:///./isolated.db",
        secret_key="a" * 32,
        environment="test",
    )
    assert settings.effective_database_url == "sqlite+aiosqlite:///./isolated.db"


def test_secret_key_requires_minimum_length() -> None:
    with pytest.raises(ValueError, match="secret_key"):
        Settings(
            database_url="sqlite+aiosqlite:///./test.db",
            secret_key="not-secure",  # noqa: S106 - intentionally invalid test value
        )
