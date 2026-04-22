from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.api.deps import (
    get_current_user,
    get_localization_service,
    get_podcast_detail_service,
    get_runtime_settings,
)
from app.api.utils import apply_locale_cookie
from app.core.config import Settings
from app.core.localization import SUPPORTED_LOCALE_CODES
from app.core.placeholders import choose_placeholder_url_stable
from app.db.models.user import UserModel
from app.services.localization import LocalizationService
from app.services.podcast_detail import PodcastDetailService, SortMode

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(tags=["Podcast Site"])

SettingsDep = Annotated[Settings, Depends(get_runtime_settings)]
LocalizationServiceDep = Annotated[
    LocalizationService, Depends(get_localization_service)
]
CurrentUserDep = Annotated[UserModel | None, Depends(get_current_user)]
PodcastDetailServiceDep = Annotated[
    PodcastDetailService, Depends(get_podcast_detail_service)
]


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

    effective_sort = _normalize_episode_sort(sort)
    episodes = await detail_service.list_episodes(feed_id=feed.id, sort=effective_sort)

    logo_url = (feed.logo_url or "").strip() or choose_placeholder_url_stable(
        feed.feed_url
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
            "is_subscribed": await detail_service.is_user_subscribed(
                current_user, feed_id=feed.id
            ),
            "is_favorited": False,
        },
    )
    apply_locale_cookie(response, settings, locale)
    return response
