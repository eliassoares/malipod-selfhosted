from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import ValidationError

from app.api.deps import get_auth_service, get_episode_service
from app.schemas.auth import AuthErrorResponse
from app.schemas.episode import (
    EpisodeActionInput,
    EpisodeActionQuery,
    EpisodeActionQueryResponse,
    EpisodeActionUploadResponse,
)
from app.services.auth import AuthError, AuthService
from app.services.episodes import EpisodeService

if TYPE_CHECKING:
    from app.db.models.user import UserModel

router = APIRouter(prefix="/api/2", tags=["Episodes API"])
security = HTTPBasic(auto_error=False)

AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
EpisodeServiceDep = Annotated[EpisodeService, Depends(get_episode_service)]


def build_unauthorized_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="authentication required",
        headers={"WWW-Authenticate": "Basic"},
    )


async def authenticate_basic_user(
    username: str,
    auth_service: AuthService,
    credentials: HTTPBasicCredentials | None,
) -> UserModel:
    if credentials is None:
        raise build_unauthorized_error()

    try:
        authenticated = await auth_service.authenticate_username(
            credentials.username,
            credentials.password,
        )
    except AuthError as exc:
        if exc.code == "invalid_login":
            raise build_unauthorized_error() from exc
        raise

    if authenticated.nickname != username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="authenticated user does not match requested username",
        )
    return authenticated


def raise_bad_request(detail: str) -> None:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


@router.post(
    "/episodes/{username}.json",
    response_model=EpisodeActionUploadResponse,
    responses={
        400: {"model": AuthErrorResponse},
        401: {"model": AuthErrorResponse},
        403: {"model": AuthErrorResponse},
    },
)
async def post_episode_actions(
    username: str,
    payload: list[dict[str, Any]],
    auth_service: AuthServiceDep,
    episode_service: EpisodeServiceDep,
    credentials: Annotated[HTTPBasicCredentials | None, Depends(security)],
) -> JSONResponse:
    user = await authenticate_basic_user(username, auth_service, credentials)
    try:
        actions = [EpisodeActionInput.model_validate(item) for item in payload]
        result = await episode_service.upload_actions(user, actions)
    except ValidationError as exc:
        raise_bad_request(exc.errors()[0]["msg"])
    except ValueError as exc:
        raise_bad_request(str(exc))

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=result.model_dump(mode="json"),
    )


@router.get(
    "/episodes/{username}.json",
    response_model=EpisodeActionQueryResponse,
    responses={
        400: {"model": AuthErrorResponse},
        401: {"model": AuthErrorResponse},
        403: {"model": AuthErrorResponse},
    },
)
async def get_episode_actions(
    username: str,
    auth_service: AuthServiceDep,
    episode_service: EpisodeServiceDep,
    credentials: Annotated[HTTPBasicCredentials | None, Depends(security)],
    podcast: str | None = None,
    device: str | None = None,
    since: int | None = None,
    aggregated: bool = False,
) -> JSONResponse:
    user = await authenticate_basic_user(username, auth_service, credentials)
    try:
        query = EpisodeActionQuery(
            podcast=podcast,
            device=device,
            since=since,
            aggregated=aggregated,
        )
        result = await episode_service.list_actions(user, query)
    except ValidationError as exc:
        raise_bad_request(exc.errors()[0]["msg"])
    except ValueError as exc:
        raise_bad_request(str(exc))

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=result.model_dump(mode="json"),
    )
