from __future__ import annotations

from typing import Annotated, NoReturn

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse

from app.api.deps import get_directory_service
from app.core.security import (
    validate_count_parameter,
    validate_settings_episode_url,
    validate_settings_podcast_url,
    validate_subscription_format,
)
from app.schemas.subscription import SubscriptionItem, SubscriptionRenderPayload
from app.services.directory import DirectoryService
from app.services.subscription_formats import SubscriptionFormatService

router = APIRouter(tags=["Directory API"])

DirectoryServiceDep = Annotated[DirectoryService, Depends(get_directory_service)]


def raise_bad_request(detail: str) -> NoReturn:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def _validate_format(value: str) -> str:
    try:
        return validate_subscription_format(value)
    except ValueError as exc:
        raise_bad_request(str(exc))


def _validate_required_query(value: str | None, *, name: str) -> str:
    if value is None:
        raise_bad_request(f"{name} is required")
    cleaned = value.strip()
    if not cleaned:
        raise_bad_request(f"{name} must not be empty")
    return cleaned


def _validate_count(value: int, *, name: str) -> int:
    try:
        return validate_count_parameter(value, name=name)
    except ValueError as exc:
        raise_bad_request(str(exc))


def _render_subscriptions(
    *,
    format_name: str,
    items: list[SubscriptionItem],
) -> Response:
    renderer = SubscriptionFormatService()
    result = renderer.render(SubscriptionRenderPayload(items=items, format=format_name))
    if isinstance(result.content, str):
        return Response(content=result.content, media_type=result.media_type)
    return JSONResponse(content=result.content, media_type=result.media_type)


@router.get("/search.{format_name}")
async def search(
    format_name: str,
    directory: DirectoryServiceDep,
    q: str | None = None,
) -> Response:
    query = _validate_required_query(q, name="q")
    normalized_format = _validate_format(format_name)

    podcasts = await directory.search_podcasts(query, limit=100)
    if normalized_format == "json":
        return JSONResponse(
            content=[item.model_dump(exclude_none=True) for item in podcasts]
        )

    items = [
        SubscriptionItem(
            url=podcast.url,
            title=podcast.title,
            description=podcast.description,
            website=podcast.website,
            logo_url=podcast.logo_url,
            mygpo_link=podcast.mygpo_link,
        )
        for podcast in podcasts
    ]
    return _render_subscriptions(format_name=normalized_format, items=items)


@router.get("/toplist/{number}.{format_name}")
async def toplist(
    number: int,
    format_name: str,
    directory: DirectoryServiceDep,
) -> Response:
    normalized_format = _validate_format(format_name)
    number = _validate_count(number, name="number")

    podcasts = await directory.toplist(number)
    if normalized_format == "json":
        return JSONResponse(
            content=[item.model_dump(exclude_none=True) for item in podcasts]
        )

    items = [
        SubscriptionItem(
            url=podcast.url,
            title=podcast.title,
            description=podcast.description,
            website=podcast.website,
            logo_url=podcast.logo_url,
            mygpo_link=podcast.mygpo_link,
        )
        for podcast in podcasts
    ]
    return _render_subscriptions(format_name=normalized_format, items=items)


@router.get("/api/2/tags/{count}.json")
async def list_tags(
    count: int,
    directory: DirectoryServiceDep,
) -> JSONResponse:
    count = _validate_count(count, name="count")
    tags = await directory.list_tags(count)
    return JSONResponse(content=[tag.model_dump() for tag in tags])


@router.get("/api/2/tag/{tag}/{count}.json")
async def list_tag_podcasts(
    tag: str,
    count: int,
    directory: DirectoryServiceDep,
) -> JSONResponse:
    cleaned_tag = tag.strip()
    if not cleaned_tag:
        raise_bad_request("tag must not be empty")
    count = _validate_count(count, name="count")

    podcasts = await directory.list_tag_podcasts(cleaned_tag, count)
    return JSONResponse(
        content=[podcast.model_dump(exclude_none=True) for podcast in podcasts]
    )


@router.get("/api/2/data/podcast.json")
async def podcast_data(
    directory: DirectoryServiceDep,
    url: str | None = None,
) -> JSONResponse:
    feed_url = _validate_required_query(url, name="url")
    try:
        normalized_url = validate_settings_podcast_url(feed_url)
    except ValueError as exc:
        raise_bad_request(str(exc))
    if normalized_url is None:
        raise_bad_request("url must be an http or https URL")

    payload = await directory.get_podcast_data(normalized_url)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    return JSONResponse(content=payload.model_dump(mode="json"))


@router.get("/api/2/data/episode.json")
async def episode_data(
    directory: DirectoryServiceDep,
    podcast: str | None = None,
    url: str | None = None,
) -> JSONResponse:
    podcast_url = _validate_required_query(podcast, name="podcast")
    media_url = _validate_required_query(url, name="url")

    try:
        normalized_podcast = validate_settings_podcast_url(podcast_url)
        normalized_url = validate_settings_episode_url(media_url)
    except ValueError as exc:
        raise_bad_request(str(exc))
    if normalized_podcast is None:
        raise_bad_request("podcast must be an http or https URL")
    if normalized_url is None:
        raise_bad_request("url must be an ASCII http or https URL")

    payload = await directory.get_episode_data(normalized_podcast, normalized_url)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    return JSONResponse(content=payload.model_dump(mode="json"))
