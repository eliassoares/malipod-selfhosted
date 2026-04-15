from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.api.deps import (
    get_auth_service,
    get_current_user,
    get_localization_service,
    get_runtime_settings,
)
from app.core.config import Settings
from app.core.localization import SUPPORTED_LOCALE_CODES
from app.db.models.user import UserModel
from app.schemas.profile import ProfilePageContext
from app.services.auth import AuthService
from app.services.localization import LocalizationService

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(tags=["Profile Site"])

SettingsDep = Annotated[Settings, Depends(get_runtime_settings)]
LocalizationServiceDep = Annotated[
    LocalizationService, Depends(get_localization_service)
]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
CurrentUserDep = Annotated[UserModel | None, Depends(get_current_user)]


def build_context(
    request: Request,
    settings: Settings,
    locale: str,
    localization_service: LocalizationService,
    user: UserModel,
) -> dict[str, object]:
    return {
        "request": request,
        "app_name": settings.app_name,
        "locale": locale,
        "copy": localization_service.build_copy(locale),
        "page_title": "Profile",
        "current_user": user,
        "profile": ProfilePageContext(
            nickname=user.nickname,
            email=user.email,
            picture_url=user.picture_url,
            language_preference=user.language_preference,
            created_at=user.created_at,
            updated_at=user.updated_at,
            accessed_at=user.accessed_at,
        ),
        "supported_locales": SUPPORTED_LOCALE_CODES,
    }


def apply_locale_cookie(
    response: HTMLResponse | RedirectResponse, settings: Settings, locale: str
) -> None:
    response.set_cookie(
        key="malipod_locale",
        value=locale,
        httponly=False,
        samesite="lax",
        secure=settings.environment == "production",
        max_age=settings.session_ttl_seconds,
    )


@router.get("/user/profile/{nickname}", response_class=HTMLResponse)
async def profile_page(
    nickname: str,
    request: Request,
    settings: SettingsDep,
    localization_service: LocalizationServiceDep,
    current_user: CurrentUserDep,
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
    ).effective_locale
    response = templates.TemplateResponse(
        request=request,
        name="profile/detail.html",
        context=build_context(
            request, settings, locale, localization_service, current_user
        ),
    )
    apply_locale_cookie(response, settings, locale)
    return response


@router.post("/user/profile/{nickname}/language")
async def update_profile_language(
    nickname: str,
    request: Request,
    settings: SettingsDep,
    auth_service: AuthServiceDep,
    current_user: CurrentUserDep,
    language_preference: str = Form(...),
) -> RedirectResponse:
    if current_user is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    if current_user.nickname != nickname:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="profile not found"
        )
    user = await auth_service.sync_user_locale(current_user, language_preference)
    response = RedirectResponse(
        url=f"/user/profile/{user.nickname}",
        status_code=status.HTTP_303_SEE_OTHER,
    )
    apply_locale_cookie(response, settings, user.language_preference)
    return response
