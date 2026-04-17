from __future__ import annotations

from json import JSONDecodeError
from typing import Annotated, NoReturn, cast

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import ValidationError

from app.api.deps import (
    authenticate_api_user,
    get_auth_service,
    get_runtime_settings,
    get_settings_service,
)
from app.core.config import Settings
from app.core.security import validate_settings_scope
from app.schemas.auth import AuthErrorResponse
from app.schemas.setting import (
    SettingsMutationRequest,
    SettingsScope,
    SettingsScopeQuery,
)
from app.services.auth import AuthService
from app.services.settings import SettingsError, SettingsService

router = APIRouter(prefix="/api/2", tags=["Settings API"])
security = HTTPBasic(auto_error=False)

AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
SettingsServiceDep = Annotated[SettingsService, Depends(get_settings_service)]
ConfigDep = Annotated[Settings, Depends(get_runtime_settings)]


def raise_bad_request(detail: str) -> NoReturn:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def build_query(
    *,
    scope: str,
    podcast: str | None,
    device: str | None,
    episode: str | None,
) -> SettingsScopeQuery:
    try:
        normalized_scope = cast("SettingsScope", validate_settings_scope(scope))
        return SettingsScopeQuery(
            scope=normalized_scope,
            podcast=podcast,
            device=device,
            episode=episode,
        )
    except ValidationError as exc:
        raise_bad_request(exc.errors()[0]["msg"])


@router.get(
    "/settings/{username}/{scope}.json",
    responses={
        400: {"model": AuthErrorResponse},
        401: {"model": AuthErrorResponse},
        403: {"model": AuthErrorResponse},
        404: {"model": AuthErrorResponse},
    },
)
async def get_settings(
    username: str,
    scope: str,
    request: Request,
    auth_service: AuthServiceDep,
    settings_service: SettingsServiceDep,
    config: ConfigDep,
    credentials: Annotated[HTTPBasicCredentials | None, Depends(security)],
    podcast: str | None = None,
    device: str | None = None,
    episode: str | None = None,
) -> JSONResponse:
    user = await authenticate_api_user(
        username, request, auth_service, config, credentials
    )
    query = build_query(
        scope=scope,
        podcast=podcast,
        device=device,
        episode=episode,
    )
    try:
        result = await settings_service.get_settings(user, query)
    except SettingsError as exc:
        if exc.code == "target_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=exc.code,
            ) from exc
        raise
    return JSONResponse(content=result.root)


@router.post(
    "/settings/{username}/{scope}.json",
    responses={
        400: {"model": AuthErrorResponse},
        401: {"model": AuthErrorResponse},
        403: {"model": AuthErrorResponse},
        404: {"model": AuthErrorResponse},
    },
)
async def post_settings(
    username: str,
    scope: str,
    request: Request,
    auth_service: AuthServiceDep,
    settings_service: SettingsServiceDep,
    config: ConfigDep,
    credentials: Annotated[HTTPBasicCredentials | None, Depends(security)],
    podcast: str | None = None,
    device: str | None = None,
    episode: str | None = None,
) -> JSONResponse:
    user = await authenticate_api_user(
        username, request, auth_service, config, credentials
    )
    query = build_query(
        scope=scope,
        podcast=podcast,
        device=device,
        episode=episode,
    )
    try:
        body = await request.json()
    except JSONDecodeError:
        raise_bad_request("request body must be a JSON object")
    if not isinstance(body, dict):
        raise_bad_request("request body must be a JSON object")
    try:
        payload = SettingsMutationRequest.model_validate(body)
        result = await settings_service.save_settings(user, query, payload)
    except ValidationError as exc:
        raise_bad_request(exc.errors()[0]["msg"])
    except ValueError as exc:
        raise_bad_request(str(exc))
    except SettingsError as exc:
        if exc.code == "target_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=exc.code,
            ) from exc
        raise
    return JSONResponse(content=result.root)
