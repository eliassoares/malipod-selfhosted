from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.services.readiness import ReadinessService


def get_runtime_settings() -> Settings:
    return get_settings()


def get_readiness_service(
    settings: Annotated[Settings, Depends(get_runtime_settings)],
) -> ReadinessService:
    return ReadinessService(settings=settings)
