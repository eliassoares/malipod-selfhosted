from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from app.db.models.podcast import EpisodeModel, PodcastFeedModel
from app.services.archive_queue import ARCHIVE_STATUS_QUEUED, get_archive_queue

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_enqueue_episode_is_idempotent(db_session: AsyncSession) -> None:
    feed = PodcastFeedModel(
        feed_url="https://example.com/feed.xml",
        title="Example Podcast",
    )
    db_session.add(feed)
    await db_session.commit()
    await db_session.refresh(feed)

    episode = EpisodeModel(
        feed_id=feed.id,
        episode_url="https://example.com/ep-1",
        title="Episode One",
        released_at=datetime.now(UTC),
    )
    db_session.add(episode)
    await db_session.commit()
    await db_session.refresh(episode)

    queue = get_archive_queue()
    first = await queue.enqueue_episode(db_session, episode_id=episode.id)
    await db_session.refresh(episode)
    assert first is True
    assert episode.archive_status == ARCHIVE_STATUS_QUEUED

    second = await queue.enqueue_episode(db_session, episode_id=episode.id)
    await db_session.refresh(episode)
    assert second is False
    assert episode.archive_status == ARCHIVE_STATUS_QUEUED
