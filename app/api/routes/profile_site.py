from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.api.deps import (
    get_auth_service,
    get_current_user,
    get_localization_service,
    get_runtime_settings,
    get_user_data_tools_service,
)
from app.api.utils import apply_locale_cookie
from app.core.config import Settings
from app.core.localization import SUPPORTED_LOCALE_CODES
from app.db.models.user import UserModel
from app.schemas.profile import ProfilePageContext
from app.schemas.user_data_tools import UserDataSnapshot
from app.services.auth import AuthService
from app.services.feed_import import import_feed_in_background
from app.services.localization import LocalizationService
from app.services.user_data_tools import UserDataToolsError, UserDataToolsService

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(tags=["Profile Site"])

SNAPSHOT_FILE_FIELD = File(...)

SettingsDep = Annotated[Settings, Depends(get_runtime_settings)]
LocalizationServiceDep = Annotated[
    LocalizationService, Depends(get_localization_service)
]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
UserDataToolsServiceDep = Annotated[
    UserDataToolsService, Depends(get_user_data_tools_service)
]
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


def _require_profile_owner(
    nickname: str,
    current_user: UserModel | None,
    settings: Settings,
    localization_service: LocalizationService,
) -> UserModel:
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="login required"
        )
    if current_user.nickname != nickname or current_user.deactivated_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=localization_service.build_copy(settings.default_locale)[
                "errors.profile_forbidden"
            ],
        )
    return current_user


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
        explicit_locale=request.query_params.get("lang"),
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


@router.post("/user/profile/{nickname}/export")
async def export_user_data(
    nickname: str,
    request: Request,
    settings: SettingsDep,
    localization_service: LocalizationServiceDep,
    current_user: CurrentUserDep,
    user_data_tools: UserDataToolsServiceDep,
) -> Response:
    if current_user is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    _require_profile_owner(nickname, current_user, settings, localization_service)
    snapshot = await user_data_tools.export_snapshot(current_user)
    filename = f"malipod_data_{datetime.now(UTC).date().isoformat()}.json"
    return Response(
        content=json.dumps(snapshot, ensure_ascii=False).encode("utf-8"),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/user/profile/{nickname}/import")
async def import_user_data(
    nickname: str,
    request: Request,
    background_tasks: BackgroundTasks,
    settings: SettingsDep,
    localization_service: LocalizationServiceDep,
    current_user: CurrentUserDep,
    user_data_tools: UserDataToolsServiceDep,
    snapshot_file: UploadFile = SNAPSHOT_FILE_FIELD,
) -> Response:
    if current_user is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    _require_profile_owner(nickname, current_user, settings, localization_service)
    max_import_bytes = 10 * 1024 * 1024
    try:
        raw = await snapshot_file.read(max_import_bytes + 1)
        if len(raw) > max_import_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail="file too large",
            )
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="invalid json"
        ) from exc
    try:
        snapshot = UserDataSnapshot.model_validate(data)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="invalid snapshot",
        ) from exc
    try:
        await user_data_tools.import_snapshot(current_user, snapshot)
    except UserDataToolsError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.code
        ) from exc

    if settings.environment != "test":
        feed_urls = {r.feed_url for r in snapshot.podcast_feeds} | {
            r.feed_url for r in snapshot.device_subscriptions
        }
        for feed_url in feed_urls:
            background_tasks.add_task(import_feed_in_background, settings, feed_url)

    return RedirectResponse(
        url=f"/user/profile/{nickname}", status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/user/profile/{nickname}/delete-data")
async def delete_user_data(
    nickname: str,
    request: Request,
    settings: SettingsDep,
    localization_service: LocalizationServiceDep,
    current_user: CurrentUserDep,
    user_data_tools: UserDataToolsServiceDep,
    confirm: str = Form(default=""),
) -> Response:
    if current_user is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    _require_profile_owner(nickname, current_user, settings, localization_service)
    if confirm.strip().upper() != "DELETE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="missing confirmation",
        )
    await user_data_tools.delete_user_data(current_user)
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(settings.session_cookie_name)
    return response


@router.post("/user/profile/{nickname}/delete-user")
async def delete_user_account(
    nickname: str,
    request: Request,
    settings: SettingsDep,
    localization_service: LocalizationServiceDep,
    auth_service: AuthServiceDep,
    current_user: CurrentUserDep,
    user_data_tools: UserDataToolsServiceDep,
    confirm: str = Form(default=""),
) -> Response:
    if current_user is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    _require_profile_owner(nickname, current_user, settings, localization_service)
    if confirm.strip().upper() != "DELETE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="missing confirmation",
        )
    session_model = await auth_service.get_active_session(
        request.cookies.get(settings.session_cookie_name)
    )
    if session_model is not None:
        await auth_service.revoke_session(session_model)
    await user_data_tools.delete_user_account(current_user)
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(settings.session_cookie_name)
    return response
