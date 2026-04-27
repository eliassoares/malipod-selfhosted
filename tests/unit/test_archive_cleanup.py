from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from app.db.models.podcast import EpisodeModel, PodcastFeedModel
from app.services.archive_cleanup import ArchiveCleanupService

if TYPE_CHECKING:
    from pathlib import Path

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.core.config import Settings


@pytest.mark.asyncio
async def test_cleanup_does_not_delete_outside_archive_dir(
    settings: Settings,
    db_session: AsyncSession,
    tmp_path: Path,
) -> None:
    outside = tmp_path / "outside.mp3"
    outside.write_bytes(b"keep")

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
    episode.archive_status = "done"
    episode.archive_path = "../outside.mp3"
    db_session.add(episode)
    await db_session.commit()
    await db_session.refresh(episode)

    service = ArchiveCleanupService(session=db_session, settings=settings)
    ok = await service.disable_archive(feed_id=feed.id)
    assert ok is True

    await db_session.refresh(episode)
    assert episode.archive_status == "none"
    assert episode.archive_path is None
    assert outside.read_bytes() == b"keep"
