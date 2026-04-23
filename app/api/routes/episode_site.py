from __future__ import annotations

import re
from typing import TYPE_CHECKING, Annotated

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from app.api.deps import (
    get_current_user,
    get_episode_detail_service,
    get_episode_favorites_service,
    get_localization_service,
    get_runtime_settings,
)
from app.api.utils import apply_locale_cookie
from app.core.config import Settings
from app.core.localization import SUPPORTED_LOCALE_CODES
from app.db.models.user import UserModel
from app.services.episode_detail import EpisodeDetailService
from app.services.episode_favorites import EpisodeFavoritesService
from app.services.localization import LocalizationService

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(tags=["Episode Site"])

SettingsDep = Annotated[Settings, Depends(get_runtime_settings)]
LocalizationServiceDep = Annotated[
    LocalizationService, Depends(get_localization_service)
]
CurrentUserDep = Annotated[UserModel | None, Depends(get_current_user)]
EpisodeDetailServiceDep = Annotated[
    EpisodeDetailService, Depends(get_episode_detail_service)
]
EpisodeFavoritesServiceDep = Annotated[
    EpisodeFavoritesService, Depends(get_episode_favorites_service)
]


@router.get("/episode/{episode_id}", response_class=HTMLResponse)
async def episode_detail_page(
    episode_id: int,
    request: Request,
    settings: SettingsDep,
    localization_service: LocalizationServiceDep,
    current_user: CurrentUserDep,
    detail_service: EpisodeDetailServiceDep,
    favorites_service: EpisodeFavoritesServiceDep,
) -> Response:
    if current_user is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    locale = localization_service.resolve_locale(
        request.cookies.get("malipod_locale"),
        user=current_user,
        explicit_locale=request.query_params.get("lang"),
    ).effective_locale
    copy = localization_service.build_copy(locale)

    episode = await detail_service.get_episode(episode_id=episode_id)
    if episode is None:
        response = templates.TemplateResponse(
            request=request,
            name="episodes/not_found.html",
            context={
                "page_title": copy.get("episode_detail.not_found_title", "Not found"),
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

    progress = await detail_service.get_progress(current_user, episode_id=episode.id)
    history = await detail_service.list_recent_history(
        current_user,
        episode_id=episode.id,
        limit=10,
    )

    episode_logo_url = detail_service.choose_episode_logo_url(episode)
    share_url = f"{settings.base_url.rstrip('/')}/episode/{episode.id}"

    response = templates.TemplateResponse(
        request=request,
        name="episodes/detail.html",
        context={
            "page_title": episode.title,
            "app_name": settings.app_name,
            "locale": locale,
            "copy": copy,
            "supported_locales": SUPPORTED_LOCALE_CODES,
            "current_user": current_user,
            "episode": episode,
            "episode_logo_url": episode_logo_url,
            "progress": progress,
            "history": history,
            "is_favorited": await favorites_service.is_favorited(
                current_user, episode_id=episode.id
            ),
            "share_url": share_url,
        },
    )
    apply_locale_cookie(response, settings, locale)
    return response


def _safe_filename(title: str, media_url: str) -> str:
    ext = ""
    path = urlparse(media_url).path
    if "." in path.rsplit("/", 1)[-1]:
        ext = "." + path.rsplit(".", 1)[-1].split("?")[0][:8]
    slug = re.sub(r"[^\w\s-]", "", title).strip()
    slug = re.sub(r"[\s]+", "_", slug)[:80]
    return f"{slug}{ext}" if slug else f"episode{ext}"


@router.get("/episode/{episode_id}/download")
async def download_episode(
    episode_id: int,
    current_user: CurrentUserDep,
    detail_service: EpisodeDetailServiceDep,
) -> Response:
    if current_user is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    episode = await detail_service.get_episode(episode_id=episode_id)
    if episode is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    media_url = (episode.media_url or "").strip()
    if not media_url or urlparse(media_url).scheme not in ("http", "https"):
        return RedirectResponse(
            url=f"/episode/{episode.id}",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    filename = _safe_filename(episode.title, media_url)
    client = httpx.AsyncClient(follow_redirects=True, timeout=30)
    upstream = await client.send(
        httpx.Request("GET", media_url),
        stream=True,
    )
    if upstream.status_code >= 400:
        await upstream.aclose()
        await client.aclose()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Media file unavailable.",
        )

    content_type = upstream.headers.get("content-type", "application/octet-stream")

    async def _stream() -> AsyncGenerator[bytes]:
        try:
            async for chunk in upstream.aiter_bytes(chunk_size=65536):
                yield chunk
        finally:
            await upstream.aclose()
            await client.aclose()

    return StreamingResponse(
        _stream(),
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": upstream.headers.get("content-length", ""),
        },
    )


@router.post("/episode/{episode_id}/favorite")
async def toggle_episode_favorite(
    episode_id: int,
    settings: SettingsDep,
    localization_service: LocalizationServiceDep,
    current_user: CurrentUserDep,
    detail_service: EpisodeDetailServiceDep,
    favorites_service: EpisodeFavoritesServiceDep,
) -> RedirectResponse:
    if current_user is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    episode = await detail_service.get_episode(episode_id=episode_id)
    if episode is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=localization_service.build_copy(settings.default_locale)[
                "episode_detail.not_found_title"
            ],
        )

    await favorites_service.toggle_favorite(current_user, episode_id=episode.id)

    return RedirectResponse(
        url=f"/episode/{episode.id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )
