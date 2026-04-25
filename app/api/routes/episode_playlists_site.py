from __future__ import annotations

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.api.deps import (
    get_current_user,
    get_episode_playlists_service,
    get_localization_service,
    get_runtime_settings,
)
from app.api.utils import apply_locale_cookie
from app.core.config import Settings
from app.core.localization import SUPPORTED_LOCALE_CODES
from app.db.models.user import UserModel
from app.services.episode_playlists import (
    EpisodePlaylistsError,
    EpisodePlaylistsService,
    PlaylistWritePayload,
)
from app.services.localization import LocalizationService

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(tags=["Episode Playlists Site"])

SettingsDep = Annotated[Settings, Depends(get_runtime_settings)]
LocalizationServiceDep = Annotated[
    LocalizationService, Depends(get_localization_service)
]
CurrentUserDep = Annotated[UserModel | None, Depends(get_current_user)]
EpisodePlaylistsServiceDep = Annotated[
    EpisodePlaylistsService, Depends(get_episode_playlists_service)
]

OPTIONAL_IMAGE_FILE = File(default=None)


def _require_owner(
    nickname: str,
    current_user: UserModel | None,
    settings: Settings,
    localization_service: LocalizationService,
) -> UserModel:
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="login required"
        )
    if current_user.nickname != nickname or current_user.deactivated_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=localization_service.build_copy(settings.default_locale)[
                "errors.profile_forbidden"
            ],
        )
    return current_user


def _read_image_upload(upload: UploadFile | None) -> tuple[str | None, bytes] | None:
    if upload is None:
        return None
    return (upload.content_type, upload.file.read())


@router.get("/user/{nickname}/playlists", response_class=HTMLResponse)
async def playlists_manage_page(
    nickname: str,
    request: Request,
    settings: SettingsDep,
    localization_service: LocalizationServiceDep,
    current_user: CurrentUserDep,
    playlists_service: EpisodePlaylistsServiceDep,
    error: str | None = None,
    success: str | None = None,
    playlist_id: int | None = None,
) -> Response:
    if current_user is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    owner = _require_owner(nickname, current_user, settings, localization_service)

    locale = localization_service.resolve_locale(
        request.cookies.get("malipod_locale"),
        user=owner,
        explicit_locale=request.query_params.get("lang"),
    ).effective_locale
    copy = localization_service.build_copy(locale)

    cards = await playlists_service.list_cards(owner)

    response = templates.TemplateResponse(
        request=request,
        name="playlists/manage.html",
        context={
            "page_title": copy.get("playlists.manage_title", "Playlists"),
            "app_name": settings.app_name,
            "locale": locale,
            "copy": copy,
            "supported_locales": SUPPORTED_LOCALE_CODES,
            "current_user": owner,
            "nickname": nickname,
            "cards": cards,
            "error": error,
            "success": success,
            "highlight_playlist_id": playlist_id,
        },
    )
    apply_locale_cookie(response, settings, locale)
    return response


@router.post("/user/{nickname}/playlists/create")
async def create_playlist(
    nickname: str,
    request: Request,
    settings: SettingsDep,
    localization_service: LocalizationServiceDep,
    current_user: CurrentUserDep,
    playlists_service: EpisodePlaylistsServiceDep,
    title: str = Form(""),
    description: str = Form(""),
    image: UploadFile | None = OPTIONAL_IMAGE_FILE,
) -> RedirectResponse:
    if current_user is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    owner = _require_owner(nickname, current_user, settings, localization_service)

    image_url: str | None = None
    if image is not None:
        raw = await image.read(1 * 1024 * 1024 + 1)
        try:
            image_url = await playlists_service.save_image_upload(
                owner,
                content_type=image.content_type,
                raw=raw,
            )
        except EpisodePlaylistsError as exc:
            return RedirectResponse(
                url=f"/user/{nickname}/playlists?error={exc.code}",
                status_code=status.HTTP_303_SEE_OTHER,
            )

    try:
        playlist_id = await playlists_service.create_playlist(
            owner,
            PlaylistWritePayload(
                title=title,
                description=description,
                image_url=image_url,
            ),
        )
    except EpisodePlaylistsError as exc:
        return RedirectResponse(
            url=f"/user/{nickname}/playlists?error={exc.code}",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return RedirectResponse(
        url=f"/user/{nickname}/playlists?success=created&playlist_id={playlist_id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/user/{nickname}/playlists/{playlist_id}/update")
async def update_playlist(
    nickname: str,
    playlist_id: int,
    request: Request,
    settings: SettingsDep,
    localization_service: LocalizationServiceDep,
    current_user: CurrentUserDep,
    playlists_service: EpisodePlaylistsServiceDep,
    title: str = Form(""),
    description: str = Form(""),
    image: UploadFile | None = OPTIONAL_IMAGE_FILE,
) -> RedirectResponse:
    if current_user is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    owner = _require_owner(nickname, current_user, settings, localization_service)

    image_url: str | None = None
    if image is not None:
        raw = await image.read(1 * 1024 * 1024 + 1)
        try:
            image_url = await playlists_service.save_image_upload(
                owner,
                content_type=image.content_type,
                raw=raw,
            )
        except EpisodePlaylistsError as exc:
            return RedirectResponse(
                url=f"/user/{nickname}/playlists?error={exc.code}",
                status_code=status.HTTP_303_SEE_OTHER,
            )

    try:
        await playlists_service.update_playlist(
            owner,
            playlist_id,
            PlaylistWritePayload(
                title=title,
                description=description,
                image_url=image_url,
            ),
        )
    except EpisodePlaylistsError as exc:
        return RedirectResponse(
            url=f"/user/{nickname}/playlists?error={exc.code}",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return RedirectResponse(
        url=f"/user/{nickname}/playlists?success=updated&playlist_id={playlist_id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/user/{nickname}/playlists/{playlist_id}/delete")
async def delete_playlist(
    nickname: str,
    playlist_id: int,
    request: Request,
    settings: SettingsDep,
    localization_service: LocalizationServiceDep,
    current_user: CurrentUserDep,
    playlists_service: EpisodePlaylistsServiceDep,
    confirm: str = Form(default=""),
) -> RedirectResponse:
    if current_user is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    owner = _require_owner(nickname, current_user, settings, localization_service)
    if confirm.strip() != "1":
        return RedirectResponse(
            url=f"/user/{nickname}/playlists?error=missing_confirmation",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    try:
        await playlists_service.delete_playlist(owner, playlist_id)
    except EpisodePlaylistsError as exc:
        return RedirectResponse(
            url=f"/user/{nickname}/playlists?error={exc.code}",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    return RedirectResponse(
        url=f"/user/{nickname}/playlists?success=deleted",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/user/{nickname}/playlists/{playlist_id}", response_class=HTMLResponse)
async def playlist_detail_page(
    nickname: str,
    playlist_id: int,
    request: Request,
    settings: SettingsDep,
    localization_service: LocalizationServiceDep,
    current_user: CurrentUserDep,
    playlists_service: EpisodePlaylistsServiceDep,
    q: str | None = None,
    error: str | None = None,
    success: str | None = None,
) -> Response:
    if current_user is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    owner = _require_owner(nickname, current_user, settings, localization_service)
    locale = localization_service.resolve_locale(
        request.cookies.get("malipod_locale"),
        user=owner,
        explicit_locale=request.query_params.get("lang"),
    ).effective_locale
    copy = localization_service.build_copy(locale)

    try:
        payload = await playlists_service.build_detail(
            owner, playlist_id, search_query=q
        )
    except EpisodePlaylistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.code,
        ) from exc

    response = templates.TemplateResponse(
        request=request,
        name="playlists/detail.html",
        context={
            "page_title": payload.card.title,
            "app_name": settings.app_name,
            "locale": locale,
            "copy": copy,
            "supported_locales": SUPPORTED_LOCALE_CODES,
            "current_user": owner,
            "nickname": nickname,
            "payload": payload,
            "error": error,
            "success": success,
        },
    )
    apply_locale_cookie(response, settings, locale)
    return response


@router.post("/user/{nickname}/playlists/{playlist_id}/items")
async def update_playlist_items(
    nickname: str,
    playlist_id: int,
    request: Request,
    settings: SettingsDep,
    localization_service: LocalizationServiceDep,
    current_user: CurrentUserDep,
    playlists_service: EpisodePlaylistsServiceDep,
    episode_id: int = Form(...),
    action: str = Form(""),
) -> RedirectResponse:
    if current_user is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    owner = _require_owner(nickname, current_user, settings, localization_service)

    cleaned_action = action.strip().lower()
    if cleaned_action not in {"add", "remove"}:
        return RedirectResponse(
            url=f"/user/{nickname}/playlists/{playlist_id}?error=invalid_action",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    try:
        if cleaned_action == "add":
            await playlists_service.add_episode(owner, playlist_id, episode_id)
            success = "episode_added"
        else:
            await playlists_service.remove_episode(owner, playlist_id, episode_id)
            success = "episode_removed"
    except EpisodePlaylistsError as exc:
        return RedirectResponse(
            url=f"/user/{nickname}/playlists/{playlist_id}?error={exc.code}",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return RedirectResponse(
        url=f"/user/{nickname}/playlists/{playlist_id}?success={success}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/user/{nickname}/episode/{episode_id}/playlists")
async def add_episode_to_playlists(
    nickname: str,
    episode_id: int,
    request: Request,
    settings: SettingsDep,
    localization_service: LocalizationServiceDep,
    current_user: CurrentUserDep,
    playlists_service: EpisodePlaylistsServiceDep,
) -> RedirectResponse:
    if current_user is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    owner = _require_owner(nickname, current_user, settings, localization_service)
    form = await request.form()
    raw_ids: list[object] = []
    if hasattr(form, "getlist"):
        raw_ids = list(form.getlist("playlist_ids"))
    parsed_ids: list[int] = []
    for raw in raw_ids:
        if not isinstance(raw, str):
            continue
        try:
            parsed_ids.append(int(raw))
        except (TypeError, ValueError):
            continue
    if not parsed_ids:
        return RedirectResponse(
            url=f"/episode/{episode_id}",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    await playlists_service.add_episode_to_playlists(
        owner,
        episode_id=episode_id,
        playlist_ids=parsed_ids,
    )
    return RedirectResponse(
        url=f"/episode/{episode_id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )
