from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.api.deps import get_readiness_service, get_runtime_settings
from app.core.config import Settings  # noqa: TC001
from app.schemas.health import ApiRootResponse, HealthStatus, ReadinessStatus
from app.services.readiness import ReadinessService  # noqa: TC001

router = APIRouter(prefix="/api/v1", tags=["Health"])

SettingsDep = Annotated["Settings", Depends(get_runtime_settings)]
ReadinessServiceDep = Annotated["ReadinessService", Depends(get_readiness_service)]


@router.get("", response_model=ApiRootResponse)
async def api_root(settings: SettingsDep) -> ApiRootResponse:
    return ApiRootResponse(name=settings.app_name, status="ready", docs="/docs")


@router.get("/health/live", response_model=HealthStatus)
async def health_live() -> HealthStatus:
    return HealthStatus(status="alive")


@router.get("/health/ready", response_model=ReadinessStatus)
async def health_ready(
    response: Response,
    service: ReadinessServiceDep,
) -> ReadinessStatus:
    readiness = await service.check()
    if readiness.status != "ready":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return readiness
