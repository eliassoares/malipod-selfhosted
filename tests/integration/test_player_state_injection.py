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


def _set_user_player_state(nickname: str, *, episode_id: int) -> None:
    db_path = _sqlite_path()
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE users
            SET
                last_episode_id = ?,
                last_position_sec = ?,
                last_queue_mode = ?,
                last_queue_ref_id = ?
            WHERE nickname = ?
            """,
            (episode_id, 42, "podcast", 1, nickname),
        )
        connection.commit()


def test_player_state_injection_is_null_when_user_has_no_state(
    client: TestClient,
) -> None:
    register_user(client, nickname="listener_1")
    api_login(client, nickname="listener_1")

    response = client.get("/user/listener_1/playlists")

    assert response.status_code == 200
    assert "window.__PLAYER_STATE__" in response.text
    assert "window.__PLAYER_STATE__ = null" in response.text


def test_player_state_injection_contains_values_when_user_has_state(
    client: TestClient,
) -> None:
    register_user(client, nickname="listener_1")
    api_login(client, nickname="listener_1")

    episode_id = _seed_feed_and_episode()
    _set_user_player_state("listener_1", episode_id=episode_id)

    response = client.get("/user/listener_1/playlists")

    assert response.status_code == 200
    assert "window.__PLAYER_STATE__" in response.text
    assert f"episodeId: {episode_id}" in response.text
    assert "positionSec: 42" in response.text
    assert 'queueMode: "podcast"' in response.text
