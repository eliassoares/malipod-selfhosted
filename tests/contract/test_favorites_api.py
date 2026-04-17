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


def seed_favorite_rows(
    settings: Settings,
    *,
    nickname: str = "listener_1",
    include_second: bool = True,
    include_optional_metadata: bool = True,
) -> None:
    db_path = sqlite_path(settings)
    now = datetime.now(UTC)
    earlier = now - timedelta(hours=2)
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
                "https://example.com/feed.xml",
                "Feed One",
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
                "https://example.com/episode-1.mp3",
                "Episode 1",
                "Episode 1 description" if include_optional_metadata else None,
                "https://example.com/episode-1" if include_optional_metadata else None,
                "https://gpodder.net/episode/1" if include_optional_metadata else None,
                earlier.isoformat(),
                now.isoformat(),
                now.isoformat(),
                "https://example.com/feed.xml",
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
                "https://example.com/episode-1.mp3",
            ),
        )
        if include_second:
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
                    "https://example.com/feed-2.xml",
                    "Feed Two",
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
                    "https://example.com/episode-2.mp3",
                    "Episode 2",
                    None,
                    None,
                    None,
                    now.isoformat(),
                    now.isoformat(),
                    now.isoformat(),
                    "https://example.com/feed-2.xml",
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
                    earlier.isoformat(),
                    now.isoformat(),
                    now.isoformat(),
                    nickname,
                    "https://example.com/episode-2.mp3",
                ),
            )
        connection.commit()


def test_get_favorites_contract_returns_ordered_items_with_metadata(
    client: TestClient,
    settings: Settings,
) -> None:
    register_user(client)
    seed_favorite_rows(settings)

    response = client.get(
        "/api/2/favorites/listener_1.json",
        auth=("listener_1", "supersecret"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert [item["title"] for item in payload] == ["Episode 1", "Episode 2"]
    assert payload[0] == {
        "title": "Episode 1",
        "url": "https://example.com/episode-1.mp3",
        "podcast_title": "Feed One",
        "podcast_url": "https://example.com/feed.xml",
        "description": "Episode 1 description",
        "website": "https://example.com/episode-1",
        "released": payload[0]["released"],
        "mygpo_link": "https://gpodder.net/episode/1",
    }


def test_get_favorites_contract_returns_empty_list_for_valid_user(
    client: TestClient,
) -> None:
    register_user(client)

    response = client.get(
        "/api/2/favorites/listener_1.json",
        auth=("listener_1", "supersecret"),
    )

    assert response.status_code == 200
    assert response.json() == []


def test_get_favorites_contract_rejects_unauthorized_and_foreign_user(
    client: TestClient,
    settings: Settings,
) -> None:
    register_user(client)
    register_user(client, nickname="listener_2")
    seed_favorite_rows(settings)

    unauthorized = client.get("/api/2/favorites/listener_1.json")
    forbidden = client.get(
        "/api/2/favorites/listener_1.json",
        auth=("listener_2", "supersecret"),
    )
    missing_user = client.get(
        "/api/2/favorites/missing-user.json",
        auth=("listener_2", "supersecret"),
    )

    assert unauthorized.status_code == 401
    assert forbidden.status_code == 403
    assert missing_user.status_code == 403


def test_get_favorites_contract_returns_null_compatible_optional_fields(
    client: TestClient,
    settings: Settings,
) -> None:
    register_user(client)
    seed_favorite_rows(
        settings,
        include_second=False,
        include_optional_metadata=False,
    )

    response = client.get(
        "/api/2/favorites/listener_1.json",
        auth=("listener_1", "supersecret"),
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "title": "Episode 1",
            "url": "https://example.com/episode-1.mp3",
            "podcast_title": "Feed One",
            "podcast_url": "https://example.com/feed.xml",
            "description": None,
            "website": None,
            "released": response.json()[0]["released"],
            "mygpo_link": None,
        }
    ]
