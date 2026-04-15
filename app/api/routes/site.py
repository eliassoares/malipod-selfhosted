from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.api.deps import get_readiness_service, get_runtime_settings
from app.core.config import Settings  # noqa: TC001
from app.schemas.site import HomePageContext
from app.services.readiness import ReadinessService  # noqa: TC001

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(tags=["Site"])
SettingsDep = Annotated["Settings", Depends(get_runtime_settings)]
ReadinessServiceDep = Annotated["ReadinessService", Depends(get_readiness_service)]


@router.get("/", response_class=HTMLResponse)
async def home_page(
    request: Request,
    settings: SettingsDep,
    service: ReadinessServiceDep,
) -> HTMLResponse:
    readiness = await service.check()
    context = HomePageContext(
        app_name=settings.app_name,
        environment=settings.environment,
        status=readiness.status,
        checks=readiness.checks,
    )
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={"page": context},
        status_code=status.HTTP_200_OK
        if readiness.status == "ready"
        else status.HTTP_503_SERVICE_UNAVAILABLE,
    )
