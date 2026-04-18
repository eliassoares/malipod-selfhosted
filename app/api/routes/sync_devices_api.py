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
    get_runtime_settings,
    get_sync_devices_service,
)
from app.core.config import Settings
from app.schemas.auth import AuthErrorResponse
from app.schemas.sync_devices import SyncDevicesMutation, SyncDevicesStatus
from app.services.auth import AuthService
from app.services.sync_devices import SyncDevicesError, SyncDevicesService

router = APIRouter(prefix="/api/2", tags=["Device Sync API"])
security = HTTPBasic(auto_error=False)
logger = logging.getLogger(__name__)

AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
SyncDevicesServiceDep = Annotated[SyncDevicesService, Depends(get_sync_devices_service)]
SettingsDep = Annotated[Settings, Depends(get_runtime_settings)]


def raise_bad_request(detail: str) -> None:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


@router.get(
    "/sync-devices/{username}.json",
    response_model=SyncDevicesStatus,
    responses={
        400: {"model": AuthErrorResponse},
        401: {"model": AuthErrorResponse},
        403: {"model": AuthErrorResponse},
    },
)
async def get_sync_status(
    username: str,
    request: Request,
    auth_service: AuthServiceDep,
    sync_service: SyncDevicesServiceDep,
    settings: SettingsDep,
    credentials: Annotated[HTTPBasicCredentials | None, Depends(security)],
) -> JSONResponse:
    user = await authenticate_api_user(
        username, request, auth_service, settings, credentials
    )
    status_payload = await sync_service.get_status(user)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=status_payload.model_dump(mode="json", by_alias=True),
    )


@router.post(
    "/sync-devices/{username}.json",
    response_model=SyncDevicesStatus,
    responses={
        400: {"model": AuthErrorResponse},
        401: {"model": AuthErrorResponse},
        403: {"model": AuthErrorResponse},
    },
)
async def post_sync_mutation(
    username: str,
    payload: dict[str, Any],
    request: Request,
    auth_service: AuthServiceDep,
    sync_service: SyncDevicesServiceDep,
    settings: SettingsDep,
    credentials: Annotated[HTTPBasicCredentials | None, Depends(security)],
) -> JSONResponse:
    user = await authenticate_api_user(
        username, request, auth_service, settings, credentials
    )
    try:
        mutation = SyncDevicesMutation.model_validate(payload)
        status_payload = await sync_service.mutate(user, mutation)
    except ValidationError as exc:
        raise_bad_request(exc.errors()[0]["msg"])
    except SyncDevicesError as exc:
        logger.warning(
            "sync-devices mutation rejected for user=%s code=%s detail=%s",
            user.nickname,
            exc.code,
            exc.detail,
        )
        if exc.code == "device_not_found":
            raise_bad_request("device_not_found")
        raise_bad_request(exc.detail or exc.code)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=status_payload.model_dump(mode="json", by_alias=True),
    )
