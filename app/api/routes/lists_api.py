from __future__ import annotations

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    Request,
    Response,
    status,
)
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.api.deps import (
    authenticate_api_user,
    get_auth_service,
    get_podcast_list_service,
    get_runtime_settings,
)
from app.core.config import Settings
from app.core.security import validate_list_format, validate_podcast_list_title
from app.schemas.auth import AuthErrorResponse
from app.schemas.podcast_list import PodcastListPathRequest, PodcastListSummary
from app.services.auth import AuthService
from app.services.podcast_lists import PodcastListError, PodcastListService

router = APIRouter(tags=["Podcast Lists API"])
security = HTTPBasic(auto_error=False)

AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
PodcastListServiceDep = Annotated[
    PodcastListService,
    Depends(get_podcast_list_service),
]
SettingsDep = Annotated[Settings, Depends(get_runtime_settings)]


def raise_bad_request(detail: str) -> None:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def raise_not_found(detail: str) -> None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


@router.get(
    "/api/2/lists/{username}.json",
    response_model=list[PodcastListSummary],
    responses={404: {"model": AuthErrorResponse}},
)
async def get_user_podcast_lists(
    username: str,
    podcast_list_service: PodcastListServiceDep,
) -> JSONResponse:
    try:
        summaries = await podcast_list_service.list_summaries(username)
    except PodcastListError as exc:
        if exc.code == "user_not_found":
            raise_not_found(exc.code)
        raise
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=[item.model_dump(mode="json") for item in summaries],
    )


@router.get(
    "/api/2/lists/{username}/list/{listname}.{format}",
    responses={400: {"model": AuthErrorResponse}, 404: {"model": AuthErrorResponse}},
)
async def get_podcast_list(
    username: str,
    listname: str,
    list_format: Annotated[str, Path(alias="format")],
    podcast_list_service: PodcastListServiceDep,
) -> Response:
    try:
        request = PodcastListPathRequest(listname=listname, format=list_format)
        rendered = await podcast_list_service.get_document(
            username, request.listname, request.format
        )
        payload = podcast_list_service.format_service.render_list(rendered)
    except ValueError as exc:
        raise_bad_request(str(exc))
    except PodcastListError as exc:
        raise_not_found(exc.code)
    if payload.media_type == "application/json":
        return JSONResponse(content=payload.content)
    return Response(content=payload.content, media_type=payload.media_type)


@router.post(
    "/api/2/lists/{username}/create.{format}",
    responses={
        400: {"model": AuthErrorResponse},
        401: {"model": AuthErrorResponse},
        403: {"model": AuthErrorResponse},
        409: {"model": AuthErrorResponse},
    },
)
async def create_podcast_list(
    username: str,
    list_format: Annotated[str, Path(alias="format")],
    request: Request,
    auth_service: AuthServiceDep,
    podcast_list_service: PodcastListServiceDep,
    settings: SettingsDep,
    credentials: Annotated[HTTPBasicCredentials | None, Depends(security)],
    title: str = Query(...),
) -> Response:
    user = await authenticate_api_user(
        username, request, auth_service, settings, credentials
    )
    try:
        format_name = validate_list_format(list_format)
        normalized_title = validate_podcast_list_title(title)
        location = await podcast_list_service.create_list(
            user,
            title=normalized_title,
            format_name=format_name,
            body=await request.body(),
        )
    except ValueError as exc:
        raise_bad_request(str(exc))
    except PodcastListError as exc:
        if exc.code == "name_conflict":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=exc.code,
            ) from exc
        raise
    return Response(
        status_code=status.HTTP_303_SEE_OTHER,
        headers={"Location": location},
    )


@router.put(
    "/api/2/lists/{username}/list/{listname}.{format}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        400: {"model": AuthErrorResponse},
        401: {"model": AuthErrorResponse},
        403: {"model": AuthErrorResponse},
        404: {"model": AuthErrorResponse},
    },
)
async def update_podcast_list(
    username: str,
    listname: str,
    list_format: Annotated[str, Path(alias="format")],
    request: Request,
    auth_service: AuthServiceDep,
    podcast_list_service: PodcastListServiceDep,
    settings: SettingsDep,
    credentials: Annotated[HTTPBasicCredentials | None, Depends(security)],
) -> Response:
    user = await authenticate_api_user(
        username, request, auth_service, settings, credentials
    )
    try:
        payload = PodcastListPathRequest(listname=listname, format=list_format)
        await podcast_list_service.update_list(
            user,
            listname=payload.listname,
            format_name=payload.format,
            body=await request.body(),
        )
    except ValueError as exc:
        raise_bad_request(str(exc))
    except PodcastListError as exc:
        raise_not_found(exc.code)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/api/2/lists/{username}/list/{listname}.{format}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        400: {"model": AuthErrorResponse},
        401: {"model": AuthErrorResponse},
        403: {"model": AuthErrorResponse},
        404: {"model": AuthErrorResponse},
    },
)
async def delete_podcast_list(
    username: str,
    listname: str,
    list_format: Annotated[str, Path(alias="format")],
    request: Request,
    auth_service: AuthServiceDep,
    podcast_list_service: PodcastListServiceDep,
    settings: SettingsDep,
    credentials: Annotated[HTTPBasicCredentials | None, Depends(security)],
) -> Response:
    user = await authenticate_api_user(
        username, request, auth_service, settings, credentials
    )
    try:
        payload = PodcastListPathRequest(listname=listname, format=list_format)
        await podcast_list_service.delete_list(user, payload.listname)
    except ValueError as exc:
        raise_bad_request(str(exc))
    except PodcastListError as exc:
        raise_not_found(exc.code)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
