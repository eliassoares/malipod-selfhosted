from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Query, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.api.deps import (
    get_auth_service,
    get_current_user,
    get_localization_service,
    get_runtime_settings,
)
from app.core.config import Settings
from app.core.localization import SUPPORTED_LOCALE_CODES
from app.db.models.user import UserModel
from app.schemas.auth import LoginInput, RegistrationInput
from app.services.auth import AuthError, AuthService
from app.services.localization import LocalizationService

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(tags=["Auth Site"])

SettingsDep = Annotated[Settings, Depends(get_runtime_settings)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
LocalizationServiceDep = Annotated[
    LocalizationService, Depends(get_localization_service)
]
CurrentUserDep = Annotated[UserModel | None, Depends(get_current_user)]


def build_context(
    request: Request,
    settings: Settings,
    locale: str,
    localization_service: LocalizationService,
    page_title: str,
    current_user: UserModel | None,
    errors: list[str] | None = None,
    form_data: dict[str, str] | None = None,
    success_message: str | None = None,
) -> dict[str, object]:
    return {
        "request": request,
        "app_name": settings.app_name,
        "locale": locale,
        "copy": localization_service.build_copy(locale),
        "page_title": page_title,
        "current_user": current_user,
        "errors": errors or [],
        "form_data": form_data or {},
        "success_message": success_message,
        "supported_locales": SUPPORTED_LOCALE_CODES,
    }


def apply_locale_cookie(response: Response, settings: Settings, locale: str) -> None:
    response.set_cookie(
        key="malipod_locale",
        value=locale,
        httponly=False,
        samesite="lax",
        secure=settings.environment == "production",
        max_age=settings.session_ttl_seconds,
    )


def apply_session_cookie(
    response: Response, settings: Settings, session_id: str
) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=session_id,
        httponly=True,
        samesite="lax",
        secure=settings.environment == "production",
        max_age=settings.session_ttl_seconds,
    )


@router.get("/register", response_class=HTMLResponse)
async def register_page(
    request: Request,
    settings: SettingsDep,
    localization_service: LocalizationServiceDep,
    current_user: CurrentUserDep,
    lang: str | None = Query(default=None),
) -> Response:
    if current_user is not None:
        return RedirectResponse(
            url=f"/user/profile/{current_user.nickname}",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    locale = localization_service.resolve_locale(
        request.cookies.get("malipod_locale"),
        explicit_locale=lang,
    ).effective_locale
    response: HTMLResponse = templates.TemplateResponse(
        request=request,
        name="auth/register.html",
        context=build_context(
            request,
            settings,
            locale,
            localization_service,
            "Register",
            current_user,
            form_data={"language_preference": locale},
        ),
    )
    apply_locale_cookie(response, settings, locale)
    return response


@router.post("/register", response_class=HTMLResponse)
async def register_user(
    request: Request,
    settings: SettingsDep,
    auth_service: AuthServiceDep,
    localization_service: LocalizationServiceDep,
    current_user: CurrentUserDep,
    nickname: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    password_confirmation: str = Form(...),
    picture_url: str = Form(default=""),
    language_preference: str = Form(default="en"),
) -> Response:
    if current_user is not None:
        return RedirectResponse(
            url=f"/user/profile/{current_user.nickname}",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    form_data = {
        "nickname": nickname,
        "email": email,
        "picture_url": picture_url,
        "language_preference": language_preference,
    }
    try:
        payload = RegistrationInput(
            nickname=nickname,
            email=email,
            password=password,
            password_confirmation=password_confirmation,
            picture_url=picture_url,
            language_preference=language_preference,
        )
        await auth_service.create_user(payload)
    except ValidationError as exc:
        locale = localization_service.resolve_locale(
            request.cookies.get("malipod_locale"),
            explicit_locale=language_preference,
        ).effective_locale
        response: Response = templates.TemplateResponse(
            request=request,
            name="auth/register.html",
            context=build_context(
                request,
                settings,
                locale,
                localization_service,
                "Register",
                None,
                [error["msg"] for error in exc.errors()],
                form_data,
            ),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
        apply_locale_cookie(response, settings, locale)
        return response
    except AuthError as exc:
        locale = localization_service.resolve_locale(
            request.cookies.get("malipod_locale"),
            explicit_locale=language_preference,
        ).effective_locale
        response = templates.TemplateResponse(
            request=request,
            name="auth/register.html",
            context=build_context(
                request,
                settings,
                locale,
                localization_service,
                "Register",
                None,
                [localization_service.build_copy(locale)["errors.user_exists"]]
                if exc.code == "user_exists"
                else [exc.code],
                form_data,
            ),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
        apply_locale_cookie(response, settings, locale)
        return response

    response = RedirectResponse(
        url="/login?created=1", status_code=status.HTTP_303_SEE_OTHER
    )
    apply_locale_cookie(response, settings, payload.language_preference)
    return response


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    settings: SettingsDep,
    localization_service: LocalizationServiceDep,
    current_user: CurrentUserDep,
    lang: str | None = Query(default=None),
    created: int | None = Query(default=None),
) -> Response:
    if current_user is not None:
        return RedirectResponse(
            url=f"/user/profile/{current_user.nickname}",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    locale = localization_service.resolve_locale(
        request.cookies.get("malipod_locale"),
        explicit_locale=lang,
    ).effective_locale
    response: Response = templates.TemplateResponse(
        request=request,
        name="auth/login.html",
        context=build_context(
            request,
            settings,
            locale,
            localization_service,
            "Login",
            current_user,
            form_data={"language_preference": locale},
            success_message="Account created successfully." if created else None,
        ),
    )
    apply_locale_cookie(response, settings, locale)
    return response


@router.post("/login", response_class=HTMLResponse)
async def login_user(
    request: Request,
    settings: SettingsDep,
    auth_service: AuthServiceDep,
    localization_service: LocalizationServiceDep,
    current_user: CurrentUserDep,
    identifier: str = Form(...),
    password: str = Form(...),
    language_preference: str = Form(default="en"),
) -> Response:
    if current_user is not None:
        return RedirectResponse(
            url=f"/user/profile/{current_user.nickname}",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    locale = localization_service.resolve_locale(
        request.cookies.get("malipod_locale"),
        explicit_locale=language_preference,
    ).effective_locale
    form_data = {
        "identifier": identifier,
        "language_preference": locale,
    }
    try:
        payload = LoginInput(identifier=identifier, password=password)
        user = await auth_service.authenticate_identifier(payload)
    except (AuthError, ValidationError):
        response: Response = templates.TemplateResponse(
            request=request,
            name="auth/login.html",
            context=build_context(
                request,
                settings,
                locale,
                localization_service,
                "Login",
                None,
                [localization_service.build_copy(locale)["errors.invalid_login"]],
                form_data,
            ),
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
        apply_locale_cookie(response, settings, locale)
        return response

    session_model = await auth_service.create_session(
        user, request.headers.get("user-agent")
    )
    response = RedirectResponse(
        url=f"/user/profile/{user.nickname}",
        status_code=status.HTTP_303_SEE_OTHER,
    )
    apply_session_cookie(response, settings, session_model.session_id)
    apply_locale_cookie(response, settings, user.language_preference)
    return response


@router.post("/logout")
async def logout_web_user(
    request: Request,
    settings: SettingsDep,
    auth_service: AuthServiceDep,
) -> RedirectResponse:
    session_model = await auth_service.get_active_session(
        request.cookies.get(settings.session_cookie_name)
    )
    if session_model is not None:
        await auth_service.revoke_session(session_model)
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(settings.session_cookie_name)
    return response
