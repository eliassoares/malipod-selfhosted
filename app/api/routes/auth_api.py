from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.api.deps import get_auth_service, get_runtime_settings
from app.core.config import Settings
from app.schemas.auth import ApiSessionResponse, AuthErrorResponse
from app.services.auth import AuthError, AuthService

router = APIRouter(prefix="/api/2/auth", tags=["Auth API"])
security = HTTPBasic(auto_error=False)

SettingsDep = Annotated[Settings, Depends(get_runtime_settings)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def build_invalid_login_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="login inválido",
        headers={"WWW-Authenticate": "Basic"},
    )


@router.post(
    "/{username}/login.json",
    response_model=ApiSessionResponse,
    responses={
        400: {"model": AuthErrorResponse},
        401: {"model": AuthErrorResponse},
    },
)
async def login_user(
    username: str,
    request: Request,
    settings: SettingsDep,
    auth_service: AuthServiceDep,
    credentials: Annotated[HTTPBasicCredentials | None, Depends(security)],
) -> JSONResponse:
    active_session = await auth_service.get_active_session(
        request.cookies.get(settings.session_cookie_name)
    )
    if active_session is not None and active_session.user.nickname != username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="session cookie belongs to a different username",
        )
    if credentials is None:
        raise build_invalid_login_error()
    if credentials.username != username:
        raise build_invalid_login_error()
    try:
        user = await auth_service.authenticate_username(username, credentials.password)
    except AuthError as exc:
        if exc.code == "invalid_login":
            raise build_invalid_login_error() from exc
        raise

    session_model = await auth_service.create_session(
        user,
        request.headers.get("user-agent"),
    )
    response = JSONResponse(
        status_code=status.HTTP_200_OK,
        content=ApiSessionResponse(
            username=user.nickname,
            status="authenticated",
        ).model_dump(),
    )
    response.set_cookie(
        key=settings.session_cookie_name,
        value=session_model.session_id,
        httponly=True,
        samesite="lax",
        secure=settings.environment == "production",
        max_age=settings.session_ttl_seconds,
    )
    return response


@router.post(
    "/{username}/logout.json",
    response_model=ApiSessionResponse,
    responses={400: {"model": AuthErrorResponse}},
)
async def logout_user(
    username: str,
    request: Request,
    settings: SettingsDep,
    auth_service: AuthServiceDep,
) -> JSONResponse:
    active_session = await auth_service.get_active_session(
        request.cookies.get(settings.session_cookie_name)
    )
    if active_session is not None and active_session.user.nickname != username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="session cookie belongs to a different username",
        )
    if active_session is not None:
        await auth_service.revoke_session(active_session)
    response = JSONResponse(
        status_code=status.HTTP_200_OK,
        content=ApiSessionResponse(username=username, status="logged_out").model_dump(),
    )
    response.delete_cookie(key=settings.session_cookie_name)
    return response
