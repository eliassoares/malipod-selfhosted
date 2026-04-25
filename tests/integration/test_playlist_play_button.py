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


def _seed_feed_and_episodes() -> tuple[int, int]:
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
                "https://example.com/audio-1.mp3",
                None,
                None,
                now.isoformat(),
                now.isoformat(),
                now.isoformat(),
            ),
        )
        e1_rowid = cursor.lastrowid
        assert e1_rowid is not None
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
                "https://example.com/episode-2",
                "Episode Two",
                None,
                None,
                "https://example.com/audio-2.mp3",
                None,
                None,
                now.isoformat(),
                now.isoformat(),
                now.isoformat(),
            ),
        )
        e2_rowid = cursor.lastrowid
        assert e2_rowid is not None
        connection.commit()
        return int(e1_rowid), int(e2_rowid)


def test_playlist_detail_includes_play_button_with_queue_ids(
    client: TestClient,
) -> None:
    register_user(client, nickname="listener_1")
    api_login(client, nickname="listener_1")

    e1, e2 = _seed_feed_and_episodes()

    created = client.post(
        "/user/listener_1/playlists/create",
        data={"title": "My Playlist", "description": ""},
        follow_redirects=False,
    )
    playlist_id = int(
        created.headers["location"].split("playlist_id=")[-1].split("&")[0]
    )

    client.post(
        f"/user/listener_1/playlists/{playlist_id}/items",
        data={"episode_id": str(e1), "action": "add"},
        follow_redirects=False,
    )
    client.post(
        f"/user/listener_1/playlists/{playlist_id}/items",
        data={"episode_id": str(e2), "action": "add"},
        follow_redirects=False,
    )

    response = client.get(f"/user/listener_1/playlists/{playlist_id}")

    assert response.status_code == 200
    assert "data-maliplayer-play-playlist" in response.text
    assert f'data-playlist-id="{playlist_id}"' in response.text
    assert f'data-episode-ids="{e1},{e2}"' in response.text
