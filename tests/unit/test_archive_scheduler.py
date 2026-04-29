from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from app.db.models.podcast import EpisodeModel, PodcastFeedModel
from app.db.session import get_session_factory
from app.services.archive_queue import ARCHIVE_STATUS_QUEUED
from app.services.archive_scheduler import ArchiveScheduler

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.core.config import Settings


@pytest.mark.asyncio
async def test_archive_scheduler_enqueues_none_episodes(
    settings: Settings, db_session: AsyncSession
) -> None:
    feed = PodcastFeedModel(feed_url="https://example.com/feed.xml", title="Podcast")
    feed.archive = True
    db_session.add(feed)
    await db_session.commit()
    await db_session.refresh(feed)

    episode = EpisodeModel(
        feed_id=feed.id,
        episode_url="https://example.com/ep-1",
        title="Episode",
        released_at=datetime.now(UTC),
    )
    db_session.add(episode)
    await db_session.commit()
    await db_session.refresh(episode)

    scheduler = ArchiveScheduler(
        session_factory=get_session_factory(settings),
        settings=settings,
    )
    enqueued = await scheduler.sync_once()
    assert enqueued == 1

    await db_session.refresh(episode)
    assert episode.archive_status == ARCHIVE_STATUS_QUEUED

    again = await scheduler.sync_once()
    assert again == 0
