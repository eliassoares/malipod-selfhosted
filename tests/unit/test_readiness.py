from __future__ import annotations

import pytest

from app.core.config import Settings
from app.services.readiness import ReadinessService


@pytest.mark.asyncio
async def test_readiness_service_reports_ready_for_valid_test_settings() -> None:
    settings = Settings(
        database_url="postgresql+asyncpg://ignored:ignored@localhost:5432/ignored",
        test_database_url="sqlite+aiosqlite:///./readiness.db",
        secret_key="a" * 32,
        environment="test",
    )
    service = ReadinessService(settings=settings)
    readiness = await service.check()
    assert readiness.status == "ready"
    assert all(check.passed for check in readiness.checks)
