from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.api.deps import (
    get_current_user,
    get_localization_service,
    get_runtime_settings,
    get_user_stats_service,
)
from app.api.utils import apply_locale_cookie
from app.core.config import Settings
from app.core.localization import SUPPORTED_LOCALE_CODES
from app.db.models.user import UserModel
from app.services.localization import LocalizationService
from app.services.user_stats import UserStatsService

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(tags=["Stats Site"])

SettingsDep = Annotated[Settings, Depends(get_runtime_settings)]
LocalizationServiceDep = Annotated[
    LocalizationService, Depends(get_localization_service)
]
CurrentUserDep = Annotated[UserModel | None, Depends(get_current_user)]
UserStatsServiceDep = Annotated[UserStatsService, Depends(get_user_stats_service)]


@router.get("/user/{nickname}/stats", response_class=HTMLResponse)
async def user_stats_page(
    nickname: str,
    request: Request,
    settings: SettingsDep,
    localization_service: LocalizationServiceDep,
    current_user: CurrentUserDep,
    stats_service: UserStatsServiceDep,
) -> Response:
    if current_user is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    if current_user.nickname != nickname or current_user.deactivated_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=localization_service.build_copy(settings.default_locale)[
                "errors.profile_forbidden"
            ],
        )

    locale = localization_service.resolve_locale(
        request.cookies.get("malipod_locale"),
        user=current_user,
        explicit_locale=request.query_params.get("lang"),
    ).effective_locale
    copy = localization_service.build_copy(locale)

    payload = await stats_service.build(current_user)

    response = templates.TemplateResponse(
        request=request,
        name="stats/user_stats.html",
        context={
            "page_title": copy["stats.title"],
            "app_name": settings.app_name,
            "locale": locale,
            "copy": copy,
            "supported_locales": SUPPORTED_LOCALE_CODES,
            "current_user": current_user,
            "stats": payload,
        },
    )
    apply_locale_cookie(response, settings, locale)
    return response
