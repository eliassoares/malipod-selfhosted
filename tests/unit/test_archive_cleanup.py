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
async def test_cleanup_resets_downloading_and_error_episodes(
    settings: Settings,
    db_session: AsyncSession,
) -> None:
    feed = PodcastFeedModel(feed_url="https://example.com/feed.xml", title="Podcast")
    feed.archive = True
    db_session.add(feed)
    await db_session.commit()
    await db_session.refresh(feed)

    ep_dl = EpisodeModel(
        feed_id=feed.id,
        episode_url="https://example.com/ep-dl",
        title="Downloading",
        released_at=datetime.now(UTC),
    )
    ep_dl.archive_status = "downloading"
    ep_err = EpisodeModel(
        feed_id=feed.id,
        episode_url="https://example.com/ep-err",
        title="Error",
        released_at=datetime.now(UTC),
    )
    ep_err.archive_status = "error"
    ep_err.archive_error = "timeout"
    ep_none = EpisodeModel(
        feed_id=feed.id,
        episode_url="https://example.com/ep-none",
        title="None",
        released_at=datetime.now(UTC),
    )
    db_session.add_all([ep_dl, ep_err, ep_none])
    await db_session.commit()
    await db_session.refresh(ep_dl)
    await db_session.refresh(ep_err)
    await db_session.refresh(ep_none)

    service = ArchiveCleanupService(session=db_session, settings=settings)
    ok = await service.disable_archive(feed_id=feed.id)
    assert ok is True

    await db_session.refresh(ep_dl)
    await db_session.refresh(ep_err)
    await db_session.refresh(ep_none)
    assert ep_dl.archive_status == "none"
    assert ep_dl.archive_error is None
    assert ep_err.archive_status == "none"
    assert ep_err.archive_error is None
    assert ep_none.archive_status == "none"


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
