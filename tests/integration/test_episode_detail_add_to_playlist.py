from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from app.core.config import get_settings
from tests.contract.test_home_page import api_login, register_user

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def _sqlite_path() -> Path:
    settings = get_settings()
    return Path(settings.test_database_url.removeprefix("sqlite+aiosqlite:///"))


def seed_feed_and_episode() -> int:
    db_path = _sqlite_path()
    now = datetime.now(UTC)
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO podcast_feeds
                (
                    feed_url,
                    title,
                    description,
                    website,
                    logo_url,
                    mygpo_link,
                    categories,
                    created_at,
                    updated_at,
                    author
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "https://example.com/feed.xml",
                "Example Podcast",
                None,
                None,
                None,
                None,
                None,
                now.isoformat(),
                now.isoformat(),
                None,
            ),
        )
        feed_rowid = cursor.lastrowid
        assert feed_rowid is not None
        feed_id = int(feed_rowid)
        cursor.execute(
            """
            INSERT INTO episodes
                (
                    feed_id,
                    episode_url,
                    title,
                    description,
                    website,
                    media_url,
                    mygpo_link,
                    logo_url,
                    released_at,
                    created_at,
                    updated_at
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                feed_id,
                "https://example.com/episode-1",
                "Episode One",
                None,
                None,
                "https://example.com/audio.mp3",
                None,
                None,
                now.isoformat(),
                now.isoformat(),
                now.isoformat(),
            ),
        )
        episode_rowid = cursor.lastrowid
        assert episode_rowid is not None
        episode_id = int(episode_rowid)
        connection.commit()
        return episode_id


def test_episode_detail_adds_to_multiple_playlists(client: TestClient) -> None:
    register_user(client, nickname="listener_1")
    api_login(client, nickname="listener_1")

    episode_id = seed_feed_and_episode()
    p1 = client.post(
        "/user/listener_1/playlists/create",
        data={"title": "P1", "description": ""},
        follow_redirects=False,
    )
    p2 = client.post(
        "/user/listener_1/playlists/create",
        data={"title": "P2", "description": ""},
        follow_redirects=False,
    )
    pid1 = int(p1.headers["location"].split("playlist_id=")[-1].split("&")[0])
    pid2 = int(p2.headers["location"].split("playlist_id=")[-1].split("&")[0])

    page = client.get(f"/episode/{episode_id}")
    assert page.status_code == 200
    assert "Add to playlist" in page.text
    assert "P1" in page.text
    assert "P2" in page.text

    added = client.post(
        f"/user/listener_1/episode/{episode_id}/playlists",
        data={"playlist_ids": [str(pid1), str(pid2)]},
        follow_redirects=False,
    )
    assert added.status_code == 303

    detail1 = client.get(f"/user/listener_1/playlists/{pid1}")
    detail2 = client.get(f"/user/listener_1/playlists/{pid2}")
    assert "Episode One" in detail1.text
    assert "Episode One" in detail2.text
