from __future__ import annotations

from typing import Annotated, Literal

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Form,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.api.deps import (
    get_current_user,
    get_device_service,
    get_localization_service,
    get_runtime_settings,
    get_settings_service,
    get_subscription_service,
    get_subscriptions_page_service,
)
from app.core.config import Settings
from app.core.localization import SUPPORTED_LOCALE_CODES
from app.core.security import sanitize_subscription_url
from app.core.settings_keys import SUBSCRIPTIONS_SORT, SUBSCRIPTIONS_VIEW_MODE
from app.db.models.user import UserModel
from app.schemas.setting import SettingsMutationRequest, SettingsScopeQuery
from app.schemas.subscription import SubscriptionRenderPayload
from app.services.devices import DeviceService
from app.services.feed_import import import_feed_in_background
from app.services.localization import LocalizationService
from app.services.settings import SettingsService
from app.services.subscription_formats import SubscriptionFormatService
from app.services.subscriptions import SubscriptionService
from app.services.subscriptions_add import SubscriptionAddService
from app.services.subscriptions_page import SubscriptionsPageService, SubscriptionsQuery

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(tags=["Subscriptions Site"])

SettingsDep = Annotated[Settings, Depends(get_runtime_settings)]
LocalizationServiceDep = Annotated[
    LocalizationService, Depends(get_localization_service)
]
CurrentUserDep = Annotated[UserModel | None, Depends(get_current_user)]
SettingsServiceDep = Annotated[SettingsService, Depends(get_settings_service)]
SubscriptionServiceDep = Annotated[
    SubscriptionService, Depends(get_subscription_service)
]
SubscriptionsPageServiceDep = Annotated[
    SubscriptionsPageService, Depends(get_subscriptions_page_service)
]
DeviceServiceDep = Annotated[DeviceService, Depends(get_device_service)]

ViewMode = Literal["list", "grid"]
SortMode = Literal["recent", "oldest"]


def apply_locale_cookie(
    response: HTMLResponse | RedirectResponse,
    settings: Settings,
    locale: str,
) -> None:
    response.set_cookie(
        key="malipod_locale",
        value=locale,
        httponly=False,
        samesite="lax",
        secure=settings.environment == "production",
        max_age=settings.session_ttl_seconds,
    )


def _normalize_view(value: str | None) -> ViewMode | None:
    if value is None:
        return None
    cleaned = value.strip().lower()
    if cleaned in {"list", "grid"}:
        return cleaned  # type: ignore[return-value]
    return None


def _normalize_sort(value: str | None) -> SortMode | None:
    if value is None:
        return None
    cleaned = value.strip().lower()
    if cleaned in {"recent", "oldest"}:
        return cleaned  # type: ignore[return-value]
    return None


@router.get("/user/subscriptions/{nickname}", response_class=HTMLResponse)
async def subscriptions_page(
    nickname: str,
    request: Request,
    settings: SettingsDep,
    localization_service: LocalizationServiceDep,
    current_user: CurrentUserDep,
    settings_service: SettingsServiceDep,
    page_service: SubscriptionsPageServiceDep,
    q: str | None = None,
    sort: str | None = None,
    view: str | None = None,
    error: str | None = None,
    success: str | None = None,
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
    copy = localization_service.build_copy(locale)

    account_settings = await settings_service.get_settings(
        current_user, SettingsScopeQuery(scope="account")
    )
    stored_view = _normalize_view(
        str(account_settings.root.get(SUBSCRIPTIONS_VIEW_MODE, ""))
    )
    stored_sort = _normalize_sort(
        str(account_settings.root.get(SUBSCRIPTIONS_SORT, ""))
    )

    effective_view: ViewMode = _normalize_view(view) or stored_view or "list"
    effective_sort: SortMode = _normalize_sort(sort) or stored_sort or "recent"

    items = await page_service.list_user_subscriptions(
        current_user,
        query=SubscriptionsQuery(q=q, sort=effective_sort),
    )

    response = templates.TemplateResponse(
        request=request,
        name="subscriptions/index.html",
        context={
            "page_title": copy.get("subscriptions.title", "Subscriptions"),
            "app_name": settings.app_name,
            "locale": locale,
            "copy": copy,
            "supported_locales": SUPPORTED_LOCALE_CODES,
            "current_user": current_user,
            "items": items,
            "q": q or "",
            "sort": effective_sort,
            "view": effective_view,
            "error": error,
            "success": success,
        },
    )
    apply_locale_cookie(response, settings, locale)
    return response


@router.post("/user/subscriptions/{nickname}/preferences")
async def update_subscription_preferences(
    nickname: str,
    settings: SettingsDep,
    localization_service: LocalizationServiceDep,
    current_user: CurrentUserDep,
    settings_service: SettingsServiceDep,
    view_mode: str = Form(""),
    sort: str = Form(""),
) -> RedirectResponse:
    if current_user is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    if current_user.nickname != nickname or current_user.deactivated_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=localization_service.build_copy(settings.default_locale)[
                "errors.profile_forbidden"
            ],
        )

    effective_view = _normalize_view(view_mode)
    effective_sort = _normalize_sort(sort)
    payload = SettingsMutationRequest(
        set={
            **({SUBSCRIPTIONS_VIEW_MODE: effective_view} if effective_view else {}),
            **({SUBSCRIPTIONS_SORT: effective_sort} if effective_sort else {}),
        }
    )
    await settings_service.save_settings(
        current_user,
        SettingsScopeQuery(scope="account"),
        payload,
    )
    return RedirectResponse(
        url=f"/user/subscriptions/{current_user.nickname}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/user/subscriptions/{nickname}/export.opml")
async def export_subscriptions_opml(
    nickname: str,
    settings: SettingsDep,
    localization_service: LocalizationServiceDep,
    current_user: CurrentUserDep,
    subscription_service: SubscriptionServiceDep,
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

    items = await subscription_service.list_account_subscriptions(current_user)
    renderer = SubscriptionFormatService()
    rendered = renderer.render(
        SubscriptionRenderPayload(items=items, format="opml", jsonp=None)
    )
    response = Response(content=rendered.content, media_type=rendered.media_type)
    response.headers["Content-Disposition"] = (
        f'attachment; filename="{nickname}-subscriptions.opml"'
    )
    return response


@router.post("/user/subscriptions/{nickname}/add")
async def add_subscription_by_url(
    nickname: str,
    background_tasks: BackgroundTasks,
    settings: SettingsDep,
    localization_service: LocalizationServiceDep,
    current_user: CurrentUserDep,
    subscription_service: SubscriptionServiceDep,
    device_service: DeviceServiceDep,
    feed_url: str = Form(""),
) -> RedirectResponse:
    if current_user is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    if current_user.nickname != nickname or current_user.deactivated_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=localization_service.build_copy(settings.default_locale)[
                "errors.profile_forbidden"
            ],
        )

    sanitized = sanitize_subscription_url(feed_url)
    if not sanitized:
        return RedirectResponse(
            url=f"/user/subscriptions/{nickname}?error=invalid_url",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    existing = await subscription_service.list_account_subscriptions(current_user)
    if any(item.url == sanitized for item in existing):
        return RedirectResponse(
            url=f"/user/subscriptions/{nickname}?error=duplicate",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    add_service = SubscriptionAddService(
        device_service=device_service,
        subscription_service=subscription_service,
    )
    await add_service.subscribe_user_to_feed(current_user, sanitized)

    if settings.environment != "test":
        background_tasks.add_task(import_feed_in_background, settings, sanitized)
    return RedirectResponse(
        url=f"/user/subscriptions/{nickname}?success=added",
        status_code=status.HTTP_303_SEE_OTHER,
    )
