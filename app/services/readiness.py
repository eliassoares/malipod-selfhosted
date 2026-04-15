from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from app.core.security import redact_database_url
from app.db.session import ping_database
from app.schemas.health import ReadinessCheck, ReadinessStatus

if TYPE_CHECKING:
    from app.core.config import Settings


class ReadinessService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def check(self) -> ReadinessStatus:
        checks: list[ReadinessCheck] = [
            ReadinessCheck(
                name="runtime_configuration",
                passed=True,
                detail=f"environment={self.settings.environment}",
            )
        ]
        try:
            await ping_database(self.settings)
            checks.append(
                ReadinessCheck(
                    name="database",
                    passed=True,
                    detail=redact_database_url(self.settings.effective_database_url),
                )
            )
        except Exception as exc:  # pragma: no cover - error path exercised in tests
            checks.append(
                ReadinessCheck(
                    name="database",
                    passed=False,
                    detail=f"{type(exc).__name__}: {exc}",
                )
            )
        status: Literal["ready", "not_ready"] = (
            "ready" if all(item.passed for item in checks) else "not_ready"
        )
        return ReadinessStatus(status=status, checks=checks)
