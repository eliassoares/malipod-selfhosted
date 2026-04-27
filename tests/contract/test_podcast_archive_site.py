from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import select

from app.db.models.podcast import EpisodeModel, PodcastFeedModel
from app.services.archive_queue import ARCHIVE_STATUS_QUEUED
from tests.contract.test_home_page import api_login, register_user
from tests.shared.subscriptions_helpers import add_episode, create_feed

if TYPE_CHECKING:
    from fastapi.testclient import TestClient
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.core.config import Settings


def test_archive_enable_logged_out_redirects_to_login(client: TestClient) -> None:
    response = client.post("/podcast/1/archive", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


@pytest.mark.asyncio
async def test_archive_enable_marks_feed_and_queues_episodes(
    client: TestClient,
    db_session: AsyncSession,
) -> None:
    register_user(client, nickname="listener_1")
    api_login(client, nickname="listener_1")

    feed = await create_feed(
        db_session,
        feed_url="https://example.com/feed.xml",
        title="Example Podcast",
    )
    ep1 = await add_episode(
        db_session,
        feed=feed,
        episode_url="https://example.com/ep-1",
        title="Episode One",
    )
    ep2 = await add_episode(
        db_session,
        feed=feed,
        episode_url="https://example.com/ep-2",
        title="Episode Two",
    )

    response = client.post(f"/podcast/{feed.id}/archive", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == f"/podcast/{feed.id}"

    feed_id = feed.id
    episode_ids = [ep1.id, ep2.id]
    db_session.expire_all()
    refreshed_feed = (
        await db_session.execute(
            select(PodcastFeedModel).where(PodcastFeedModel.id == feed_id)
        )
    ).scalar_one()
    assert refreshed_feed.archive is True

    rows = (
        await db_session.execute(
            select(EpisodeModel.id, EpisodeModel.archive_status).where(
                EpisodeModel.id.in_(episode_ids)
            )
        )
    ).all()
    assert {row[0] for row in rows} == set(episode_ids)
    assert all(status == ARCHIVE_STATUS_QUEUED for _, status in rows)


@pytest.mark.asyncio
async def test_archive_disable_clears_flags_and_removes_files(
    client: TestClient,
    settings: Settings,
    db_session: AsyncSession,
    tmp_path: Path,
) -> None:
    register_user(client, nickname="listener_1")
    api_login(client, nickname="listener_1")

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
    assert response.headers["location"] == f"/podcast/{feed.id}"

    feed_id = feed.id
    db_session.expire_all()
    refreshed_feed = (
        await db_session.execute(
            select(PodcastFeedModel).where(PodcastFeedModel.id == feed_id)
        )
    ).scalar_one()
    assert refreshed_feed.archive is False

    await db_session.refresh(episode)
    assert episode.archive_status == "none"
    assert episode.archive_path is None
    assert not file_path.exists()
