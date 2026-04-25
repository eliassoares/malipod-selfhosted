from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user, get_web_player_service
from app.db.models.user import UserModel
from app.schemas.web_player import (
    EpisodeInfoResponse,
    NextEpisodeResponse,
    OkResponse,
    PlayerActionInput,
    PlayerStateInput,
)
from app.services.web_player import WebPlayerError, WebPlayerService

router = APIRouter(tags=["Web Player"])

CurrentUserDep = Annotated[UserModel | None, Depends(get_current_user)]
WebPlayerServiceDep = Annotated[WebPlayerService, Depends(get_web_player_service)]


@router.post("/web/player/state", response_model=OkResponse)
async def save_player_state(
    payload: PlayerStateInput,
    current_user: CurrentUserDep,
    player_service: WebPlayerServiceDep,
) -> OkResponse:
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="login required"
        )
    try:
        await player_service.upsert_state(current_user, payload)
    except WebPlayerError as exc:
        raise HTTPException(status_code=404, detail=exc.code) from exc
    return OkResponse()


@router.post("/web/player/action", response_model=OkResponse)
async def register_player_action(
    payload: PlayerActionInput,
    current_user: CurrentUserDep,
    player_service: WebPlayerServiceDep,
) -> OkResponse:
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="login required"
        )
    try:
        await player_service.record_action(current_user, payload)
    except WebPlayerError as exc:
        raise HTTPException(status_code=404, detail=exc.code) from exc
    return OkResponse()


@router.get("/web/episode/{episode_id}/next", response_model=NextEpisodeResponse)
async def get_next_episode(
    episode_id: int,
    current_user: CurrentUserDep,
    player_service: WebPlayerServiceDep,
) -> NextEpisodeResponse:
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="login required"
        )
    try:
        next_id = await player_service.get_next_episode_id(episode_id=episode_id)
    except WebPlayerError as exc:
        raise HTTPException(status_code=404, detail=exc.code) from exc
    return NextEpisodeResponse(episode_id=next_id)


@router.get("/web/episode/{episode_id}/info", response_model=EpisodeInfoResponse)
async def get_episode_info(
    episode_id: int,
    current_user: CurrentUserDep,
    player_service: WebPlayerServiceDep,
) -> EpisodeInfoResponse:
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="login required"
        )
    try:
        info = await player_service.get_episode_info(episode_id=episode_id)
    except WebPlayerError as exc:
        raise HTTPException(status_code=404, detail=exc.code) from exc
    return EpisodeInfoResponse.model_validate(info)
