from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy import select

from app.api.deps import get_current_user, get_request_session, get_runtime_settings
from app.core.config import Settings
from app.db.models.podcast import EpisodeModel, PodcastFeedModel
from app.db.models.user import UserModel
from app.services.archive_cleanup import ArchiveCleanupService
from app.services.archive_paths import resolve_archive_path
from app.services.archive_queue import (
    ARCHIVE_STATUS_DONE,
    ARCHIVE_STATUS_NONE,
    get_archive_queue,
)

router = APIRouter(tags=["Podcast Archive Site"])

SettingsDep = Annotated[Settings, Depends(get_runtime_settings)]
SessionDep = Annotated[Any, Depends(get_request_session)]
CurrentUserDep = Annotated[UserModel | None, Depends(get_current_user)]


@router.post("/podcast/{feed_id}/archive")
async def enable_podcast_archive(
    feed_id: int,
    settings: SettingsDep,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> Response:
    if current_user is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    feed = (
        await session.execute(
            select(PodcastFeedModel).where(PodcastFeedModel.id == feed_id)
        )
    ).scalar_one_or_none()
    if feed is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="podcast not found"
        )

    feed.archive = True
    await session.commit()

    queue = get_archive_queue()
    episode_ids = [
        row[0]
        for row in (
            await session.execute(
                select(EpisodeModel.id).where(
                    EpisodeModel.feed_id == feed_id,
                    EpisodeModel.archive_status == ARCHIVE_STATUS_NONE,
                )
            )
        ).all()
    ]
    for episode_id in episode_ids:
        await queue.enqueue_episode(session, episode_id=episode_id)

    return RedirectResponse(
        url=f"/podcast/{feed_id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.delete("/podcast/{feed_id}/archive")
async def disable_podcast_archive(
    feed_id: int,
    settings: SettingsDep,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> Response:
    if current_user is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    cleanup = ArchiveCleanupService(session=session, settings=settings)
    ok = await cleanup.disable_archive(feed_id=feed_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="podcast not found"
        )
    return RedirectResponse(
        url=f"/podcast/{feed_id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/podcast/{feed_id}/archive/episodes/{episode_id}/file")
async def download_archived_episode(
    feed_id: int,
    episode_id: int,
    settings: SettingsDep,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> Response:
    if current_user is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    episode = (
        await session.execute(
            select(EpisodeModel).where(
                EpisodeModel.id == episode_id,
                EpisodeModel.feed_id == feed_id,
                EpisodeModel.archive_status == ARCHIVE_STATUS_DONE,
            )
        )
    ).scalar_one_or_none()
    if episode is None or not episode.archive_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="file not found"
        )

    archive_root = Path(settings.archive_dir)
    full_path = resolve_archive_path(archive_root, episode.archive_path)
    if not full_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="file not found"
        )

    return FileResponse(
        path=str(full_path),
        filename=full_path.name,
        media_type="audio/mpeg",
    )
