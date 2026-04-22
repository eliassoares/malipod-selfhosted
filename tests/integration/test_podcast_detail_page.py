from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from tests.integration.test_profile_page import register_and_login

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

    from app.core.config import Settings


def sqlite_path(settings: Settings) -> Path:
    return Path(settings.test_database_url.removeprefix("sqlite+aiosqlite:///"))


def seed_podcast(settings: Settings) -> int:
    db_path = sqlite_path(settings)
    now = datetime.now(UTC)
    older = now - timedelta(days=7)
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO podcast_feeds
                (
                    feed_url, title, author, description, website, logo_url, mygpo_link,
                    categories, created_at, updated_at
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "https://example.com/feed.xml",
                "Example Podcast",
                "Example Author",
                "A description for the podcast.",
                "https://example.com",
                None,
                None,
                None,
                now.isoformat(),
                now.isoformat(),
            ),
        )
        feed_rowid = cursor.lastrowid
        assert feed_rowid is not None
        feed_id = int(feed_rowid)
        cursor.execute(
            """
            INSERT INTO episodes
                (
                    feed_id, episode_url, title, description, website, mygpo_link,
                    logo_url, released_at, created_at, updated_at
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                feed_id,
                "https://example.com/ep-1",
                "Episode One",
                "Ep 1 description",
                None,
                None,
                None,
                older.isoformat(),
                now.isoformat(),
                now.isoformat(),
            ),
        )
        cursor.execute(
            """
            INSERT INTO episodes
                (
                    feed_id, episode_url, title, description, website, mygpo_link,
                    logo_url, released_at, created_at, updated_at
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                feed_id,
                "https://example.com/ep-2",
                "Episode Two",
                None,
                None,
                None,
                None,
                now.isoformat(),
                now.isoformat(),
                now.isoformat(),
            ),
        )
        connection.commit()
        return feed_id


def test_podcast_detail_page_returns_404_for_missing_feed(
    client: TestClient,
    settings: Settings,
) -> None:
    register_and_login(client)

    response = client.get("/podcast/999999")

    assert response.status_code == 404
    assert "Podcast não encontrado" in response.text
    assert '<html lang="pt-BR">' in response.text


def test_podcast_detail_page_renders_metadata_and_episodes(
    client: TestClient,
    settings: Settings,
) -> None:
    register_and_login(client)
    feed_id = seed_podcast(settings)

    response = client.get(f"/podcast/{feed_id}")

    assert response.status_code == 200
    assert "Example Podcast" in response.text
    assert "Episódios" in response.text
    assert "/static/placeholders/" in response.text


def test_podcast_detail_page_supports_episode_sorting(
    client: TestClient,
    settings: Settings,
) -> None:
    register_and_login(client)
    feed_id = seed_podcast(settings)

    recent = client.get(f"/podcast/{feed_id}")
    oldest = client.get(f"/podcast/{feed_id}?sort=oldest")

    assert recent.status_code == 200
    assert oldest.status_code == 200

    assert recent.text.index("Episode Two") < recent.text.index("Episode One")
    assert oldest.text.index("Episode One") < oldest.text.index("Episode Two")
