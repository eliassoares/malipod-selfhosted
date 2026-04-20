from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.api.deps import (
    get_current_user,
    get_localization_service,
    get_readiness_service,
    get_runtime_settings,
)
from app.core.config import Settings  # noqa: TC001
from app.core.localization import SUPPORTED_LOCALE_CODES
from app.services.localization import LocalizationService  # noqa: TC001
from app.services.readiness import ReadinessService  # noqa: TC001

if TYPE_CHECKING:
    from app.db.models.user import UserModel

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(tags=["Site"])
SettingsDep = Annotated["Settings", Depends(get_runtime_settings)]
ReadinessServiceDep = Annotated["ReadinessService", Depends(get_readiness_service)]
LocalizationServiceDep = Annotated[
    "LocalizationService", Depends(get_localization_service)
]
CurrentUserDep = Annotated["UserModel | None", Depends(get_current_user)]


@router.get("/", response_class=HTMLResponse)
async def home_page(
    request: Request,
    settings: SettingsDep,
    service: ReadinessServiceDep,
    localization_service: LocalizationServiceDep,
    current_user: CurrentUserDep,
) -> Response:
    readiness = await service.check()

    explicit_locale = request.query_params.get("lang")
    locale = localization_service.resolve_locale(
        request.cookies.get("malipod_locale"),
        user=current_user,
        explicit_locale=explicit_locale,
    ).effective_locale
    copy = localization_service.build_copy(locale)

    response: Response = templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "page_title": copy.get("nav.home", "Home"),
            "app_name": settings.app_name,
            "locale": locale,
            "copy": copy,
            "supported_locales": SUPPORTED_LOCALE_CODES,
            "current_user": current_user,
            "readiness": readiness,
        },
        status_code=status.HTTP_200_OK
        if readiness.status == "ready"
        else status.HTTP_503_SERVICE_UNAVAILABLE,
    )

    response.set_cookie(
        key="malipod_locale",
        value=locale,
        httponly=False,
        samesite="lax",
        secure=settings.environment == "production",
        max_age=settings.session_ttl_seconds,
    )
    return response
