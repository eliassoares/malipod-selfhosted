from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
from sqlalchemy import select

from app.db.models.podcast import EpisodeModel, PodcastFeedModel
from app.services.archive_paths import (
    build_episode_archive_relpath,
    resolve_archive_path,
)
from app.services.archive_queue import (
    ARCHIVE_STATUS_DONE,
    ARCHIVE_STATUS_DOWNLOADING,
    ARCHIVE_STATUS_ERROR,
    ARCHIVE_STATUS_NONE,
    ARCHIVE_STATUS_QUEUED,
    get_archive_queue,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from app.core.config import Settings


class ArchiveWorker:
    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession],
        settings: Settings,
    ) -> None:
        self.session_factory = session_factory
        self.settings = settings
        self.queue = get_archive_queue()

    async def run(self) -> None:
        try:
            while True:
                episode_id = await self.queue.get()
                try:
                    await self._process_episode(episode_id)
                finally:
                    self.queue.task_done()
        except asyncio.CancelledError:
            raise

    async def _process_episode(self, episode_id: int) -> None:
        archive_root = Path(self.settings.archive_dir)
        async with self.session_factory() as session:
            row = (
                await session.execute(
                    select(EpisodeModel, PodcastFeedModel)
                    .join(PodcastFeedModel, PodcastFeedModel.id == EpisodeModel.feed_id)
                    .where(EpisodeModel.id == episode_id)
                )
            ).one_or_none()
            if row is None:
                return

            episode, feed = row
            if not feed.archive:
                return

            already_done = {ARCHIVE_STATUS_DONE, ARCHIVE_STATUS_DOWNLOADING}
            if episode.archive_status in already_done:
                return
            if episode.archive_status != ARCHIVE_STATUS_QUEUED:
                return

            if not (episode.media_url or "").strip():
                episode.archive_status = ARCHIVE_STATUS_ERROR
                episode.archive_error = "missing media_url"
                await session.commit()
                return

            episode.archive_status = ARCHIVE_STATUS_DOWNLOADING
            episode.archive_error = None
            await session.commit()

            relpath = build_episode_archive_relpath(
                podcast_title=feed.title,
                episode_title=episode.title,
                episode_url=episode.media_url or episode.episode_url,
            )
            full_path = resolve_archive_path(archive_root, relpath)
            full_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = full_path.with_suffix(full_path.suffix + ".part")
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)

            try:
                async with (
                    httpx.AsyncClient(follow_redirects=True, timeout=60) as client,
                    client.stream("GET", episode.media_url) as response,
                ):
                    response.raise_for_status()
                    with tmp_path.open("wb") as handle:
                        async for chunk in response.aiter_bytes():
                            if chunk:
                                handle.write(chunk)
                tmp_path.replace(full_path)

                await session.refresh(feed)
                if not feed.archive:
                    full_path.unlink(missing_ok=True)
                    episode.archive_status = ARCHIVE_STATUS_NONE
                    episode.archive_error = None
                    await session.commit()
                    return

                episode.archive_status = ARCHIVE_STATUS_DONE
                episode.archive_path = relpath
                episode.archive_error = None
                await session.commit()
            except (httpx.HTTPError, OSError, ValueError) as exc:
                if tmp_path.exists():
                    tmp_path.unlink(missing_ok=True)
                episode.archive_status = ARCHIVE_STATUS_ERROR
                episode.archive_error = str(exc)[:2048]
                await session.commit()


def build_workers(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> list[asyncio.Task[None]]:
    workers: list[asyncio.Task[None]] = []
    for _ in range(settings.archive_workers):
        worker = ArchiveWorker(session_factory=session_factory, settings=settings)
        workers.append(asyncio.create_task(worker.run()))
    return workers
