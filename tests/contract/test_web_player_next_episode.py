from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from app.core.config import get_settings
from tests.contract.test_home_page import api_login, register_user

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def _sqlite_path() -> Path:
    settings = get_settings()
    return Path(settings.test_database_url.removeprefix("sqlite+aiosqlite:///"))


def _seed_feed_with_three_episodes() -> tuple[int, int, int]:
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
        feed_id = cursor.lastrowid
        assert feed_id is not None
        released_1 = now - timedelta(days=2)
        released_2 = now - timedelta(days=1)
        released_3 = now
        ids: list[int] = []
        released = (released_1, released_2, released_3)
        for idx, released_at in enumerate(released, start=1):
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
                    int(feed_id),
                    f"https://example.com/episode-{idx}",
                    f"Episode {idx}",
                    None,
                    None,
                    f"https://example.com/audio-{idx}.mp3",
                    None,
                    None,
                    released_at.isoformat(),
                    now.isoformat(),
                    now.isoformat(),
                ),
            )
            rowid = cursor.lastrowid
            assert rowid is not None
            ids.append(int(rowid))
        connection.commit()
        return ids[0], ids[1], ids[2]


def test_next_episode_returns_previous_by_release_date(client: TestClient) -> None:
    register_user(client, nickname="listener_1")
    api_login(client, nickname="listener_1")

    oldest, middle, newest = _seed_feed_with_three_episodes()

    response = client.get(f"/web/episode/{newest}/next")
    assert response.status_code == 200
    assert response.json() == {"episode_id": middle}

    response2 = client.get(f"/web/episode/{middle}/next")
    assert response2.status_code == 200
    assert response2.json() == {"episode_id": oldest}

    response3 = client.get(f"/web/episode/{oldest}/next")
    assert response3.status_code == 200
    assert response3.json() == {"episode_id": None}
