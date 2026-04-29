from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from sqlalchemy import select

from app.db.models.podcast import EpisodeModel, PodcastFeedModel
from app.services.archive_queue import ARCHIVE_STATUS_NONE, get_archive_queue

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from app.core.config import Settings


class ArchiveScheduler:
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
        interval = self.settings.archive_sync_interval_minutes * 60
        try:
            while True:
                await self.sync_once()
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            raise

    async def sync_once(self) -> int:
        enqueued = 0
        async with self.session_factory() as session:
            statement = (
                select(EpisodeModel.id)
                .join(PodcastFeedModel, PodcastFeedModel.id == EpisodeModel.feed_id)
                .where(
                    PodcastFeedModel.archive.is_(True),
                    EpisodeModel.archive_status == ARCHIVE_STATUS_NONE,
                )
            )
            ids = [row[0] for row in (await session.execute(statement)).all()]
            for episode_id in ids:
                if await self.queue.enqueue_episode(session, episode_id=episode_id):
                    enqueued += 1
        return enqueued


def start_scheduler(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> asyncio.Task[None]:
    scheduler = ArchiveScheduler(session_factory=session_factory, settings=settings)
    return asyncio.create_task(scheduler.run())
