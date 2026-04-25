from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
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


def seed_episode_action_history(
    settings: Settings,
    *,
    nickname: str = "listener_1",
) -> None:
    db_path = sqlite_path(settings)
    now = datetime.now(UTC)
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
                "Feed",
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
                None,
                None,
                None,
                now.isoformat(),
                now.isoformat(),
                now.isoformat(),
                "https://example.com/feed.xml",
            ),
        )
        cursor.execute(
            """
            INSERT INTO episode_action_events
                (
                    user_id, episode_id, podcast_url, episode_url, device_id,
                    action, occurred_at, started, position, total, created_at
                )
            SELECT users.id, episodes.id, ?, ?, ?, ?, ?, ?, ?, ?, ?
            FROM users, episodes
            WHERE users.nickname = ? AND episodes.episode_url = ?
            """,
            (
                "https://example.com/feed.xml",
                "https://example.com/episode-1.mp3",
                "phone-01",
                "download",
                now.isoformat(),
                None,
                None,
                None,
                now.isoformat(),
                nickname,
                "https://example.com/episode-1.mp3",
            ),
        )
        connection.commit()


def test_post_episode_actions_contract_returns_timestamp_and_update_urls(
    client: TestClient,
) -> None:
    register_user(client)

    response = client.post(
        "/api/2/episodes/listener_1.json",
        auth=("listener_1", "supersecret"),
        json=[
            {
                "podcast": " https://example.com/feed.xml ",
                "episode": "https://example.com/episode-1.mp3 ",
                "device": "phone-01",
                "action": "download",
            },
            {
                "podcast": "https://example.com/feed.xml",
                "episode": "ftp://invalid.example/episode.ogg",
                "action": "delete",
            },
        ],
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["timestamp"] >= 1
    assert payload["update_urls"] == [
        [" https://example.com/feed.xml ", "https://example.com/feed.xml"],
        ["https://example.com/episode-1.mp3 ", "https://example.com/episode-1.mp3"],
        ["ftp://invalid.example/episode.ogg", ""],
    ]


def test_post_episode_actions_contract_rejects_invalid_play_payload(
    client: TestClient,
) -> None:
    register_user(client)

    response = client.post(
        "/api/2/episodes/listener_1.json",
        auth=("listener_1", "supersecret"),
        json=[
            {
                "podcast": "https://example.com/feed.xml",
                "episode": "https://example.com/episode-1.mp3",
                "action": "play",
                "started": 15,
                "position": 120,
            }
        ],
    )

    assert response.status_code == 400
    assert "play/pause actions require" in response.json()["detail"]


def test_get_episode_actions_contract_supports_since_and_filters(
    client: TestClient,
    settings: Settings,
) -> None:
    register_user(client)
    seed_episode_action_history(settings)
    uploaded = client.post(
        "/api/2/episodes/listener_1.json",
        auth=("listener_1", "supersecret"),
        json=[
            {
                "podcast": "https://example.com/feed.xml",
                "episode": "https://example.com/episode-1.mp3",
                "device": "phone-01",
                "action": "play",
                "started": 10,
                "position": 50,
                "total": 100,
            },
            {
                "podcast": "https://example.com/feed-two.xml",
                "episode": "https://example.com/episode-2.mp3",
                "device": "tablet-01",
                "action": "delete",
            },
        ],
    )
    baseline = client.get(
        "/api/2/episodes/listener_1.json?since=0",
        auth=("listener_1", "supersecret"),
    )
    since = client.get(
        "/api/2/episodes/listener_1.json?since=1",
        auth=("listener_1", "supersecret"),
    )
    filtered = client.get(
        "/api/2/episodes/listener_1.json?device=phone-01&podcast=https://example.com/feed.xml&aggregated=true",
        auth=("listener_1", "supersecret"),
    )

    assert uploaded.status_code == 200
    assert baseline.status_code == 200
    assert baseline.json()["timestamp"] == uploaded.json()["timestamp"]
    assert len(since.json()["actions"]) == 2
    assert filtered.status_code == 200
    assert len(filtered.json()["actions"]) == 1
    assert filtered.json()["actions"][0]["action"] == "play"


def test_get_episode_actions_contract_rejects_foreign_user(
    client: TestClient,
) -> None:
    register_user(client)
    register_user(client, nickname="listener_2")

    response = client.get(
        "/api/2/episodes/listener_1.json",
        auth=("listener_2", "supersecret"),
    )

    assert response.status_code == 403
