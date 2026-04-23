from __future__ import annotations

import asyncio
from typing import Annotated, Any

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
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
    get_podcast_detail_service,
    get_podcast_favorites_service,
    get_runtime_settings,
    get_subscription_service,
)
from app.api.utils import apply_locale_cookie
from app.core.config import Settings
from app.core.localization import SUPPORTED_LOCALE_CODES
from app.core.placeholders import choose_placeholder_url_stable
from app.db.models.user import UserModel
from app.services.devices import DeviceService
from app.services.feed_import import import_feed_in_background
from app.services.localization import LocalizationService
from app.services.podcast_detail import PodcastDetailService, SortMode
from app.services.podcast_favorites import PodcastFavoritesService
from app.services.subscriptions import SubscriptionService
from app.services.subscriptions_add import SubscriptionAddService

templates = Jinja2Templates(directory="app/templates")


async def _gather(*coros: Any) -> tuple[Any, ...]:
    return tuple(await asyncio.gather(*coros))


router = APIRouter(tags=["Podcast Site"])

SettingsDep = Annotated[Settings, Depends(get_runtime_settings)]
LocalizationServiceDep = Annotated[
    LocalizationService, Depends(get_localization_service)
]
CurrentUserDep = Annotated[UserModel | None, Depends(get_current_user)]
PodcastDetailServiceDep = Annotated[
    PodcastDetailService, Depends(get_podcast_detail_service)
]
PodcastFavoritesServiceDep = Annotated[
    PodcastFavoritesService, Depends(get_podcast_favorites_service)
]
SubscriptionServiceDep = Annotated[
    SubscriptionService, Depends(get_subscription_service)
]
DeviceServiceDep = Annotated[DeviceService, Depends(get_device_service)]


def _normalize_episode_sort(value: str | None) -> SortMode:
    if value is None:
        return "recent"
    cleaned = value.strip().lower()
    if cleaned == "oldest":
        return "oldest"
    return "recent"


@router.get("/podcast/{feed_id}", response_class=HTMLResponse)
async def podcast_detail_page(
    feed_id: int,
    request: Request,
    settings: SettingsDep,
    localization_service: LocalizationServiceDep,
    current_user: CurrentUserDep,
    detail_service: PodcastDetailServiceDep,
    favorites_service: PodcastFavoritesServiceDep,
    sort: str | None = None,
) -> Response:
    if current_user is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    locale = localization_service.resolve_locale(
        request.cookies.get("malipod_locale"),
        user=current_user,
        explicit_locale=request.query_params.get("lang"),
    ).effective_locale
    copy = localization_service.build_copy(locale)

    feed = await detail_service.get_feed(feed_id=feed_id)
    if feed is None:
        response = templates.TemplateResponse(
            request=request,
            name="podcasts/not_found.html",
            context={
                "page_title": copy.get("podcast_detail.not_found_title", "Not found"),
                "app_name": settings.app_name,
                "locale": locale,
                "copy": copy,
                "supported_locales": SUPPORTED_LOCALE_CODES,
                "current_user": current_user,
            },
            status_code=status.HTTP_404_NOT_FOUND,
        )
        apply_locale_cookie(response, settings, locale)
        return response

    logo_url = (feed.logo_url or "").strip() or choose_placeholder_url_stable(
        feed.feed_url
    )

    effective_sort = _normalize_episode_sort(sort)
    episodes, listening_stats, is_subscribed, is_favorited = await _gather(
        detail_service.list_episodes(
            feed_id=feed.id,
            sort=effective_sort,
            fallback_logo_url=logo_url,
            user=current_user,
        ),
        detail_service.get_listening_stats(current_user, feed_id=feed.id),
        detail_service.is_user_subscribed(current_user, feed_id=feed.id),
        favorites_service.is_favorited(current_user, feed_id=feed.id),
    )

    response = templates.TemplateResponse(
        request=request,
        name="podcasts/detail.html",
        context={
            "page_title": feed.title,
            "app_name": settings.app_name,
            "locale": locale,
            "copy": copy,
            "supported_locales": SUPPORTED_LOCALE_CODES,
            "current_user": current_user,
            "feed": feed,
            "feed_logo_url": logo_url,
            "episodes": episodes,
            "sort": effective_sort,
            "is_subscribed": is_subscribed,
            "is_favorited": is_favorited,
            "listening_stats": listening_stats,
        },
    )
    apply_locale_cookie(response, settings, locale)
    return response


@router.post("/podcast/{feed_id}/subscribe")
async def subscribe_to_podcast(
    feed_id: int,
    background_tasks: BackgroundTasks,
    settings: SettingsDep,
    localization_service: LocalizationServiceDep,
    current_user: CurrentUserDep,
    detail_service: PodcastDetailServiceDep,
    subscription_service: SubscriptionServiceDep,
    device_service: DeviceServiceDep,
) -> RedirectResponse:
    if current_user is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    feed = await detail_service.get_feed(feed_id=feed_id)
    if feed is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=localization_service.build_copy(settings.default_locale)[
                "podcast_detail.not_found_title"
            ],
        )

    if await detail_service.is_user_subscribed(current_user, feed_id=feed.id):
        return RedirectResponse(
            url=f"/podcast/{feed.id}",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    add_service = SubscriptionAddService(
        device_service=device_service,
        subscription_service=subscription_service,
    )
    await add_service.subscribe_user_to_feed(current_user, feed.feed_url)

    if settings.environment != "test":
        background_tasks.add_task(import_feed_in_background, settings, feed.feed_url)

    return RedirectResponse(
        url=f"/podcast/{feed.id}?success=subscribed",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/podcast/{feed_id}/unsubscribe")
async def unsubscribe_from_podcast(
    feed_id: int,
    settings: SettingsDep,
    localization_service: LocalizationServiceDep,
    current_user: CurrentUserDep,
    detail_service: PodcastDetailServiceDep,
    subscription_service: SubscriptionServiceDep,
    device_service: DeviceServiceDep,
) -> RedirectResponse:
    if current_user is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    feed = await detail_service.get_feed(feed_id=feed_id)
    if feed is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=localization_service.build_copy(settings.default_locale)[
                "podcast_detail.not_found_title"
            ],
        )

    if not await detail_service.is_user_subscribed(current_user, feed_id=feed.id):
        return RedirectResponse(
            url=f"/podcast/{feed.id}",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    remove_service = SubscriptionAddService(
        device_service=device_service,
        subscription_service=subscription_service,
    )
    await remove_service.unsubscribe_user_from_feed(current_user, feed.feed_url)

    return RedirectResponse(
        url=f"/podcast/{feed.id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/podcast/{feed_id}/favorite")
async def toggle_podcast_favorite(
    feed_id: int,
    settings: SettingsDep,
    localization_service: LocalizationServiceDep,
    current_user: CurrentUserDep,
    detail_service: PodcastDetailServiceDep,
    favorites_service: PodcastFavoritesServiceDep,
) -> RedirectResponse:
    if current_user is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    feed = await detail_service.get_feed(feed_id=feed_id)
    if feed is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=localization_service.build_copy(settings.default_locale)[
                "podcast_detail.not_found_title"
            ],
        )

    await favorites_service.toggle_favorite(current_user, feed_id=feed.id)

    return RedirectResponse(
        url=f"/podcast/{feed.id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )
