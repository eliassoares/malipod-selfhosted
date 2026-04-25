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


def seed_feed_and_episode(*, nickname: str = "listener_1") -> int:
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


def test_playlist_detail_page_renders_with_placeholder(client: TestClient) -> None:
    register_user(client, nickname="listener_1")
    api_login(client, nickname="listener_1")

    created = client.post(
        "/user/listener_1/playlists/create",
        data={"title": "My Playlist", "description": ""},
        follow_redirects=False,
    )
    playlist_id = int(
        created.headers["location"].split("playlist_id=")[-1].split("&")[0]
    )

    response = client.get(f"/user/listener_1/playlists/{playlist_id}")

    assert response.status_code == 200
    assert "My Playlist" in response.text
    assert "/static/placeholders/" in response.text


def test_playlist_detail_page_adds_and_removes_episode(client: TestClient) -> None:
    register_user(client, nickname="listener_1")
    api_login(client, nickname="listener_1")

    episode_id = seed_feed_and_episode()
    created = client.post(
        "/user/listener_1/playlists/create",
        data={"title": "My Playlist", "description": ""},
        follow_redirects=False,
    )
    playlist_id = int(
        created.headers["location"].split("playlist_id=")[-1].split("&")[0]
    )

    search = client.get(f"/user/listener_1/playlists/{playlist_id}?q=Episode")
    assert search.status_code == 200
    assert "Episode One" in search.text

    added = client.post(
        f"/user/listener_1/playlists/{playlist_id}/items",
        data={"episode_id": str(episode_id), "action": "add"},
        follow_redirects=False,
    )
    assert added.status_code == 303

    detail = client.get(f"/user/listener_1/playlists/{playlist_id}")
    assert detail.status_code == 200
    assert "Episode One" in detail.text

    removed = client.post(
        f"/user/listener_1/playlists/{playlist_id}/items",
        data={"episode_id": str(episode_id), "action": "remove"},
        follow_redirects=False,
    )
    assert removed.status_code == 303

    detail_after = client.get(f"/user/listener_1/playlists/{playlist_id}")
    assert detail_after.status_code == 200
    assert "Episode One" not in detail_after.text
