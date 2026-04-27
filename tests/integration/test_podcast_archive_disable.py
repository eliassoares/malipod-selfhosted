from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import select

from app.db.models.podcast import PodcastFeedModel
from tests.integration.test_profile_page import register_and_login
from tests.shared.subscriptions_helpers import add_episode, create_feed

if TYPE_CHECKING:
    from fastapi.testclient import TestClient
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.core.config import Settings


@pytest.mark.asyncio
async def test_disable_archive_resets_episode_fields_and_deletes_file(
    client: TestClient,
    settings: Settings,
    db_session: AsyncSession,
) -> None:
    register_and_login(client)
    feed = await create_feed(
        db_session,
        feed_url="https://example.com/feed.xml",
        title="Example Podcast",
    )
    episode = await add_episode(
        db_session,
        feed=feed,
        episode_url="https://example.com/ep-1",
        title="Episode One",
    )
    feed.archive = True
    episode.archive_status = "done"
    episode.archive_path = "example/episode.mp3"
    await db_session.commit()

    archive_dir = Path(settings.archive_dir)
    file_path = archive_dir / episode.archive_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(b"test")

    response = client.delete(f"/podcast/{feed.id}/archive", follow_redirects=False)
    assert response.status_code == 303

    refreshed_feed = (
        await db_session.execute(
            select(PodcastFeedModel).where(PodcastFeedModel.id == feed.id)
        )
    ).scalar_one()
    assert refreshed_feed.archive is False

    await db_session.refresh(episode)
    assert episode.archive_status == "none"
    assert episode.archive_path is None
    assert not file_path.exists()
