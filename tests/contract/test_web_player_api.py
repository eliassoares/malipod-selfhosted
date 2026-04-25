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


def _seed_feed_and_episode() -> int:
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
        episode_rowid = cursor.lastrowid
        assert episode_rowid is not None
        connection.commit()
        return int(episode_rowid)


def test_web_player_state_persists_user_fields(client: TestClient) -> None:
    register_user(client, nickname="listener_1")
    api_login(client, nickname="listener_1")
    episode_id = _seed_feed_and_episode()

    response = client.post(
        "/web/player/state",
        json={
            "episode_id": episode_id,
            "position_sec": 12,
            "queue_mode": "podcast",
            "queue_ref_id": 1,
        },
    )
    assert response.status_code == 200
    assert response.json() == {"ok": True}

    page = client.get("/user/listener_1/playlists")
    assert page.status_code == 200
    assert f"episodeId: {episode_id}" in page.text


def test_web_player_action_creates_device_and_inserts_event(client: TestClient) -> None:
    register_user(client, nickname="listener_1")
    api_login(client, nickname="listener_1")
    episode_id = _seed_feed_and_episode()

    response = client.post(
        "/web/player/action",
        json={
            "episode_id": episode_id,
            "action": "play",
            "started": 0,
            "position": 5,
            "total": 120,
        },
    )
    assert response.status_code == 200
    assert response.json() == {"ok": True}

    db_path = _sqlite_path()
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM devices WHERE device_id = ?",
            ("web-player",),
        )
        assert int(cursor.fetchone()[0]) == 1
        cursor.execute(
            "SELECT action, device_id, episode_id "
            "FROM episode_action_events "
            "ORDER BY id DESC LIMIT 1"
        )
        action, device_id, stored_episode_id = cursor.fetchone()
        assert action == "play"
        assert device_id == "web-player"
        assert int(stored_episode_id) == episode_id
