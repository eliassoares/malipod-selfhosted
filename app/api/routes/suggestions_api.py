from __future__ import annotations

import json as json_module
from typing import TYPE_CHECKING, Annotated, NoReturn

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse

from app.api.deps import get_directory_service, get_required_current_user
from app.core.security import (
    validate_count_parameter,
    validate_jsonp_callback,
    validate_subscription_format,
)
from app.schemas.subscription import SubscriptionItem, SubscriptionRenderPayload
from app.services.directory import DirectoryService
from app.services.subscription_formats import SubscriptionFormatService

router = APIRouter(tags=["Suggestions API"])

DirectoryServiceDep = Annotated[DirectoryService, Depends(get_directory_service)]
if TYPE_CHECKING:
    from app.db.models.user import UserModel

CurrentUserDep = Annotated["UserModel", Depends(get_required_current_user)]


def raise_bad_request(detail: str) -> NoReturn:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def _validate_format(value: str) -> str:
    try:
        return validate_subscription_format(value)
    except ValueError as exc:
        raise_bad_request(str(exc))


def _validate_number(value: int) -> int:
    try:
        return validate_count_parameter(value, name="number")
    except ValueError as exc:
        raise_bad_request(str(exc))


def _validate_jsonp(value: str | None) -> str | None:
    try:
        return validate_jsonp_callback(value)
    except ValueError as exc:
        raise_bad_request(str(exc))


def _render_subscriptions(
    *, format_name: str, items: list[SubscriptionItem]
) -> Response:
    renderer = SubscriptionFormatService()
    result = renderer.render(SubscriptionRenderPayload(items=items, format=format_name))
    if isinstance(result.content, str):
        return Response(content=result.content, media_type=result.media_type)
    return JSONResponse(content=result.content, media_type=result.media_type)


@router.get("/suggestions/{number}.{format_name}")
async def suggestions(
    number: int,
    format_name: str,
    directory: DirectoryServiceDep,
    current_user: CurrentUserDep,
    jsonp: str | None = None,
) -> Response:
    normalized_format = _validate_format(format_name)
    number = _validate_number(number)
    callback = _validate_jsonp(jsonp)

    podcasts = await directory.suggestions_for_user(current_user.id, number)
    if normalized_format == "json":
        content = [item.model_dump(exclude_none=True) for item in podcasts]
        if callback:
            body = f"{callback}({json_module.dumps(content)});"
            return Response(content=body, media_type="application/javascript")
        return JSONResponse(content=content)

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
