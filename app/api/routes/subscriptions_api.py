from __future__ import annotations

from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Path,
    Request,
    Response,
    status,
)
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.api.deps import (
    authenticate_api_user,
    get_auth_service,
    get_runtime_settings,
    get_subscription_service,
)
from app.core.config import Settings
from app.core.security import (
    validate_device_id,
    validate_jsonp_callback,
    validate_since_timestamp,
    validate_subscription_format,
)
from app.schemas.auth import AuthErrorResponse
from app.schemas.subscription import SubscriptionItem, SubscriptionRenderPayload
from app.services.auth import AuthService
from app.services.feed_import import import_feed_in_background
from app.services.subscription_formats import SubscriptionFormatService
from app.services.subscriptions import SubscriptionError, SubscriptionService

router = APIRouter(tags=["Subscriptions API"])
security = HTTPBasic(auto_error=False)

AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
SubscriptionServiceDep = Annotated[
    SubscriptionService,
    Depends(get_subscription_service),
]
SettingsDep = Annotated[Settings, Depends(get_runtime_settings)]


def raise_bad_request(detail: str) -> None:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def build_read_response(
    *,
    items: list[SubscriptionItem],
    format_name: str,
    jsonp: str | None,
) -> Response:
    renderer = SubscriptionFormatService()
    rendered = renderer.render(
        SubscriptionRenderPayload(
            items=items,
            format=format_name,
            jsonp=jsonp,
        )
    )
    if rendered.media_type == "application/json":
        return JSONResponse(content=rendered.content)
    return Response(content=rendered.content, media_type=rendered.media_type)


@router.get(
    "/subscriptions/{username}.{format}",
    responses={
        400: {"model": AuthErrorResponse},
        401: {"model": AuthErrorResponse},
        403: {"model": AuthErrorResponse},
    },
)
async def get_account_subscriptions(
    username: str,
    subscription_format: Annotated[str, Path(alias="format")],
    request: Request,
    auth_service: AuthServiceDep,
    subscription_service: SubscriptionServiceDep,
    settings: SettingsDep,
    credentials: Annotated[HTTPBasicCredentials | None, Depends(security)],
    jsonp: str | None = None,
) -> Response:
    user = await authenticate_api_user(
        username, request, auth_service, settings, credentials
    )
    try:
        format_name = validate_subscription_format(subscription_format)
        callback = validate_jsonp_callback(jsonp)
        if callback is not None and format_name != "json":
            raise_bad_request("jsonp is only supported for json format")
    except ValueError as exc:
        raise_bad_request(str(exc))
    items = await subscription_service.list_account_subscriptions(user)
    return build_read_response(items=items, format_name=format_name, jsonp=callback)


@router.get(
    "/subscriptions/{username}/{deviceid}.{format}",
    responses={
        400: {"model": AuthErrorResponse},
        401: {"model": AuthErrorResponse},
        403: {"model": AuthErrorResponse},
        404: {"model": AuthErrorResponse},
    },
)
async def get_device_subscriptions(
    username: str,
    deviceid: str,
    subscription_format: Annotated[str, Path(alias="format")],
    request: Request,
    auth_service: AuthServiceDep,
    subscription_service: SubscriptionServiceDep,
    settings: SettingsDep,
    credentials: Annotated[HTTPBasicCredentials | None, Depends(security)],
    jsonp: str | None = None,
) -> Response:
    user = await authenticate_api_user(
        username, request, auth_service, settings, credentials
    )
    try:
        validate_device_id(deviceid)
        format_name = validate_subscription_format(subscription_format)
        callback = validate_jsonp_callback(jsonp)
        if callback is not None and format_name != "json":
            raise_bad_request("jsonp is only supported for json format")
        items = await subscription_service.list_device_subscriptions(user, deviceid)
    except ValueError as exc:
        raise_bad_request(str(exc))
    except SubscriptionError as exc:
        if exc.code == "device_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=exc.code,
            ) from exc
        raise
    return build_read_response(items=items, format_name=format_name, jsonp=callback)


@router.put(
    "/subscriptions/{username}/{deviceid}.{format}",
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": AuthErrorResponse},
        401: {"model": AuthErrorResponse},
        403: {"model": AuthErrorResponse},
    },
)
async def put_device_subscriptions(
    username: str,
    deviceid: str,
    subscription_format: Annotated[str, Path(alias="format")],
    request: Request,
    background_tasks: BackgroundTasks,
    auth_service: AuthServiceDep,
    subscription_service: SubscriptionServiceDep,
    settings: SettingsDep,
    credentials: Annotated[HTTPBasicCredentials | None, Depends(security)],
) -> Response:
    user = await authenticate_api_user(
        username, request, auth_service, settings, credentials
    )
    parser = SubscriptionFormatService()
    try:
        validate_device_id(deviceid)
        format_name = validate_subscription_format(subscription_format)
        imported = parser.parse_upload(format_name, await request.body())
        await subscription_service.replace_device_subscriptions(
            user,
            deviceid,
            imported,
        )
    except ValueError as exc:
        raise_bad_request(str(exc))
    if settings.environment != "test":
        for item in imported:
            background_tasks.add_task(import_feed_in_background, settings, item.url)
    return Response(status_code=status.HTTP_200_OK, content=b"")


@router.post(
    "/api/2/subscriptions/{username}/{deviceid}.json",
    responses={
        400: {"model": AuthErrorResponse},
        401: {"model": AuthErrorResponse},
        403: {"model": AuthErrorResponse},
        404: {"model": AuthErrorResponse},
    },
)
async def post_subscription_changes(
    username: str,
    deviceid: str,
    request: Request,
    background_tasks: BackgroundTasks,
    auth_service: AuthServiceDep,
    subscription_service: SubscriptionServiceDep,
    settings: SettingsDep,
    credentials: Annotated[HTTPBasicCredentials | None, Depends(security)],
) -> JSONResponse:
    user = await authenticate_api_user(
        username, request, auth_service, settings, credentials
    )
    add_urls: list[str] = []
    try:
        validate_device_id(deviceid)
        payload = await request.json()
        if not isinstance(payload, dict):
            raise_bad_request("request body must be a JSON object")
        add = payload.get("add", [])
        remove = payload.get("remove", [])
        if not isinstance(add, list) or not isinstance(remove, list):
            raise_bad_request("add and remove must be arrays")
        add_urls = [str(item) for item in add]
        result = await subscription_service.apply_delta(
            user,
            deviceid,
            add_urls,
            [str(item) for item in remove],
        )
    except ValueError as exc:
        raise_bad_request(str(exc))
    except SubscriptionError as exc:
        if exc.code == "device_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=exc.code,
            ) from exc
        if exc.code == "conflicting_delta":
            raise_bad_request(exc.code)
        raise
    if settings.environment != "test":
        for url in add_urls:
            background_tasks.add_task(import_feed_in_background, settings, url)
    return JSONResponse(content=result.model_dump(mode="json"))


@router.get(
    "/api/2/subscriptions/{username}/{deviceid}.json",
    responses={
        400: {"model": AuthErrorResponse},
        401: {"model": AuthErrorResponse},
        403: {"model": AuthErrorResponse},
        404: {"model": AuthErrorResponse},
    },
)
async def get_subscription_changes(
    username: str,
    deviceid: str,
    request: Request,
    auth_service: AuthServiceDep,
    subscription_service: SubscriptionServiceDep,
    settings: SettingsDep,
    credentials: Annotated[HTTPBasicCredentials | None, Depends(security)],
    since: int | None = None,
) -> JSONResponse:
    user = await authenticate_api_user(
        username, request, auth_service, settings, credentials
    )
    try:
        validate_device_id(deviceid)
        validated_since = validate_since_timestamp(since)
        result = await subscription_service.get_changes(user, deviceid, validated_since)
    except ValueError as exc:
        raise_bad_request(str(exc))
    except SubscriptionError as exc:
        if exc.code == "device_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=exc.code,
            ) from exc
        raise
    return JSONResponse(content=result.model_dump(mode="json"))
