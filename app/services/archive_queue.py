from __future__ import annotations

import asyncio
import weakref
from typing import TYPE_CHECKING

from sqlalchemy import select

from app.db.models.podcast import EpisodeModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


ARCHIVE_STATUS_NONE = "none"
ARCHIVE_STATUS_QUEUED = "queued"
ARCHIVE_STATUS_DOWNLOADING = "downloading"
ARCHIVE_STATUS_DONE = "done"
ARCHIVE_STATUS_ERROR = "error"

ACTIVE_ARCHIVE_STATUSES = {
    ARCHIVE_STATUS_QUEUED,
    ARCHIVE_STATUS_DOWNLOADING,
    ARCHIVE_STATUS_DONE,
}


class ArchiveQueue:
    def __init__(self) -> None:
        self._queue: asyncio.Queue[int] = asyncio.Queue()

    async def enqueue_episode(self, session: AsyncSession, *, episode_id: int) -> bool:
        """Idempotently enqueue an episode for archival download.

        Returns True if the episode was newly queued, False if it was already active.
        """
        episode = (
            await session.execute(
                select(EpisodeModel).where(EpisodeModel.id == episode_id)
            )
        ).scalar_one_or_none()
        if episode is None:
            return False
        if episode.archive_status in ACTIVE_ARCHIVE_STATUSES:
            return False
        episode.archive_status = ARCHIVE_STATUS_QUEUED
        episode.archive_error = None
        await session.commit()
        await self._queue.put(episode_id)
        return True

    async def cancel_episode(self, session: AsyncSession, *, episode_id: int) -> bool:
        episode = (
            await session.execute(
                select(EpisodeModel).where(EpisodeModel.id == episode_id)
            )
        ).scalar_one_or_none()
        if episode is None:
            return False
        if episode.archive_status != ARCHIVE_STATUS_QUEUED:
            return False
        episode.archive_status = ARCHIVE_STATUS_NONE
        await session.commit()
        return True

    async def get(self) -> int:
        return await self._queue.get()

    def task_done(self) -> None:
        self._queue.task_done()

    async def join(self) -> None:
        await self._queue.join()


def get_archive_queue() -> ArchiveQueue:
    loop = asyncio.get_running_loop()
    queue = _singleton_by_loop.get(loop)
    if queue is None:
        queue = ArchiveQueue()
        _singleton_by_loop[loop] = queue
    return queue


_singleton_by_loop: weakref.WeakKeyDictionary[
    asyncio.AbstractEventLoop, ArchiveQueue
] = weakref.WeakKeyDictionary()
