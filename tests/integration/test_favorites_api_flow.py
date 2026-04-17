from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

    from app.core.config import Settings


def register_user(client: TestClient, nickname: str = "listener_1") -> None:
    response = client.post(
        "/register",
        data={
            "nickname": nickname,
            "email": f"{nickname}@example.com",
            "password": "supersecret",
            "password_confirmation": "supersecret",
            "picture_url": "",
            "language_preference": "en",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303


def sqlite_path(settings: Settings) -> Path:
    return Path(settings.test_database_url.removeprefix("sqlite+aiosqlite:///"))


def seed_favorites(
    settings: Settings,
    *,
    nickname: str = "listener_1",
) -> None:
    db_path = sqlite_path(settings)
    now = datetime.now(UTC)
    older = now - timedelta(days=1)
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO podcast_feeds
                (
                    feed_url, title, description, website, logo_url, mygpo_link,
                    created_at, updated_at
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "https://example.com/feed-a.xml",
                "Feed A",
                None,
                None,
                None,
                None,
                now.isoformat(),
                now.isoformat(),
            ),
        )
        cursor.execute(
            """
            INSERT INTO episodes
                (
                    feed_id, episode_url, title, description, website, mygpo_link,
                    released_at, created_at, updated_at
                )
            SELECT id, ?, ?, ?, ?, ?, ?, ?, ? FROM podcast_feeds WHERE feed_url = ?
            """,
            (
                "https://example.com/episode-a.mp3",
                "Episode A",
                "Desc A",
                "https://example.com/a",
                "https://gpodder.net/episode/a",
                older.isoformat(),
                now.isoformat(),
                now.isoformat(),
                "https://example.com/feed-a.xml",
            ),
        )
        cursor.execute(
            """
            INSERT INTO podcast_feeds
                (
                    feed_url, title, description, website, logo_url, mygpo_link,
                    created_at, updated_at
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "https://example.com/feed-b.xml",
                "Feed B",
                None,
                None,
                None,
                None,
                now.isoformat(),
                now.isoformat(),
            ),
        )
        cursor.execute(
            """
            INSERT INTO episodes
                (
                    feed_id, episode_url, title, description, website, mygpo_link,
                    released_at, created_at, updated_at
                )
            SELECT id, ?, ?, ?, ?, ?, ?, ?, ? FROM podcast_feeds WHERE feed_url = ?
            """,
            (
                "https://example.com/episode-b.mp3",
                "Episode B",
                None,
                None,
                None,
                now.isoformat(),
                now.isoformat(),
                now.isoformat(),
                "https://example.com/feed-b.xml",
            ),
        )
        cursor.execute(
            """
            INSERT INTO favorite_episodes
                (user_id, episode_id, favorited_at, created_at, updated_at)
            SELECT users.id, episodes.id, ?, ?, ?
            FROM users, episodes
            WHERE users.nickname = ? AND episodes.episode_url = ?
            """,
            (
                now.isoformat(),
                now.isoformat(),
                now.isoformat(),
                nickname,
                "https://example.com/episode-a.mp3",
            ),
        )
        cursor.execute(
            """
            INSERT INTO favorite_episodes
                (user_id, episode_id, favorited_at, created_at, updated_at)
            SELECT users.id, episodes.id, ?, ?, ?
            FROM users, episodes
            WHERE users.nickname = ? AND episodes.episode_url = ?
            """,
            (
                older.isoformat(),
                now.isoformat(),
                now.isoformat(),
                nickname,
                "https://example.com/episode-b.mp3",
            ),
        )
        connection.commit()


def test_favorites_flow_reads_ordered_favorites_for_authenticated_owner(
    client: TestClient,
    settings: Settings,
) -> None:
    register_user(client)
    seed_favorites(settings)

    response = client.get(
        "/api/2/favorites/listener_1.json",
        auth=("listener_1", "supersecret"),
    )

    assert response.status_code == 200
    assert [item["title"] for item in response.json()] == ["Episode A", "Episode B"]


def test_favorites_flow_returns_empty_list_when_user_has_no_favorites(
    client: TestClient,
) -> None:
    register_user(client)

    response = client.get(
        "/api/2/favorites/listener_1.json",
        auth=("listener_1", "supersecret"),
    )

    assert response.status_code == 200
    assert response.json() == []


def test_favorites_flow_rejects_cross_account_and_unknown_user_reads(
    client: TestClient,
    settings: Settings,
) -> None:
    register_user(client)
    register_user(client, nickname="listener_2")
    seed_favorites(settings)

    denied = client.get(
        "/api/2/favorites/listener_1.json",
        auth=("listener_2", "supersecret"),
    )
    missing = client.get(
        "/api/2/favorites/missing-user.json",
        auth=("listener_2", "supersecret"),
    )

    assert denied.status_code == 403
    assert missing.status_code == 404


def test_favorites_flow_requires_authentication(
    client: TestClient,
    settings: Settings,
) -> None:
    register_user(client)
    seed_favorites(settings)

    response = client.get("/api/2/favorites/listener_1.json")

    assert response.status_code == 401
