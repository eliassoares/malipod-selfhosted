from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import ValidationError

from app.api.deps import (
    authenticate_api_user,
    get_auth_service,
    get_device_service,
    get_runtime_settings,
)
from app.core.config import Settings
from app.core.security import validate_device_id
from app.schemas.auth import AuthErrorResponse
from app.schemas.device import (
    DeviceMutationPayload,
    DeviceSummary,
    DeviceUpdatesResponse,
    DeviceUpsertRequest,
)
from app.services.auth import AuthService
from app.services.devices import DeviceError, DeviceService

router = APIRouter(prefix="/api/2", tags=["Device API"])
security = HTTPBasic(auto_error=False)

AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
DeviceServiceDep = Annotated[DeviceService, Depends(get_device_service)]
SettingsDep = Annotated[Settings, Depends(get_runtime_settings)]


def raise_bad_request(detail: str) -> None:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


@router.post(
    "/devices/{username}/{deviceid}.json",
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": AuthErrorResponse},
        401: {"model": AuthErrorResponse},
        403: {"model": AuthErrorResponse},
    },
)
async def upsert_device(
    username: str,
    deviceid: str,
    payload: DeviceMutationPayload,
    request: Request,
    auth_service: AuthServiceDep,
    device_service: DeviceServiceDep,
    settings: SettingsDep,
    credentials: Annotated[HTTPBasicCredentials | None, Depends(security)],
) -> Response:
    user = await authenticate_api_user(
        username, request, auth_service, settings, credentials
    )
    try:
        request_payload = DeviceUpsertRequest(
            device_id=deviceid,
            **payload.model_dump(exclude_none=True),
        )
    except ValidationError as exc:
        raise_bad_request(exc.errors()[0]["msg"])

    await device_service.upsert_device(user, request_payload)
    return Response(status_code=status.HTTP_200_OK)


@router.get(
    "/devices/{username}.json",
    response_model=list[DeviceSummary],
    responses={
        401: {"model": AuthErrorResponse},
        403: {"model": AuthErrorResponse},
    },
)
async def list_devices(
    username: str,
    request: Request,
    auth_service: AuthServiceDep,
    device_service: DeviceServiceDep,
    settings: SettingsDep,
    credentials: Annotated[HTTPBasicCredentials | None, Depends(security)],
) -> list[DeviceSummary]:
    user = await authenticate_api_user(
        username, request, auth_service, settings, credentials
    )
    return await device_service.list_devices_for_user(user)


@router.get(
    "/updates/{username}/{deviceid}.json",
    response_model=DeviceUpdatesResponse,
    responses={
        400: {"model": AuthErrorResponse},
        401: {"model": AuthErrorResponse},
        403: {"model": AuthErrorResponse},
        404: {"model": AuthErrorResponse},
    },
)
async def get_device_updates(
    username: str,
    deviceid: str,
    request: Request,
    auth_service: AuthServiceDep,
    device_service: DeviceServiceDep,
    settings: SettingsDep,
    credentials: Annotated[HTTPBasicCredentials | None, Depends(security)],
    since: Annotated[int | None, Query(ge=0)] = None,
    include_actions: bool = False,
) -> JSONResponse:
    user = await authenticate_api_user(
        username, request, auth_service, settings, credentials
    )
    try:
        validate_device_id(deviceid)
        payload = await device_service.get_updates_for_device(
            user,
            deviceid,
            since,
            include_actions,
        )
    except ValueError as exc:
        raise_bad_request(str(exc))
    except DeviceError as exc:
        if exc.code == "device_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=exc.code,
            ) from exc
        raise

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=payload.model_dump(mode="json"),
    )
