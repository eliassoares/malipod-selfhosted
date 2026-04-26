from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import ValidationError

from app.api.deps import (
    authenticate_api_user,
    get_auth_service,
    get_episode_service,
    get_runtime_settings,
)
from app.core.config import Settings
from app.schemas.auth import AuthErrorResponse
from app.schemas.episode import (
    EpisodeActionInput,
    EpisodeActionQuery,
    EpisodeActionQueryResponse,
    EpisodeActionUploadResponse,
)
from app.services.auth import AuthService
from app.services.episodes import EpisodeService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/2", tags=["Episodes API"])
security = HTTPBasic(auto_error=False)

AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
EpisodeServiceDep = Annotated[EpisodeService, Depends(get_episode_service)]
SettingsDep = Annotated[Settings, Depends(get_runtime_settings)]


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
    request: Request,
    auth_service: AuthServiceDep,
    episode_service: EpisodeServiceDep,
    settings: SettingsDep,
    credentials: Annotated[HTTPBasicCredentials | None, Depends(security)],
) -> JSONResponse:
    user = await authenticate_api_user(
        username, request, auth_service, settings, credentials
    )
    logger.info(
        "episode_actions_upload: user=%s count=%d payload=%s",
        username,
        len(payload),
        payload,
    )
    try:
        actions = [EpisodeActionInput.model_validate(item) for item in payload]
        result = await episode_service.upload_actions(user, actions)
    except ValidationError as exc:
        logger.warning(
            "episode_actions_upload validation error: user=%s error=%s payload=%s",
            username,
            exc.errors(),
            payload,
        )
        raise_bad_request(exc.errors()[0]["msg"])
    except ValueError as exc:
        logger.warning(
            "episode_actions_upload value error: user=%s error=%s payload=%s",
            username,
            str(exc),
            payload,
        )
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
    request: Request,
    auth_service: AuthServiceDep,
    episode_service: EpisodeServiceDep,
    settings: SettingsDep,
    credentials: Annotated[HTTPBasicCredentials | None, Depends(security)],
    podcast: str | None = None,
    device: str | None = None,
    since: int | None = None,
    aggregated: bool = False,
) -> JSONResponse:
    user = await authenticate_api_user(
        username, request, auth_service, settings, credentials
    )
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
