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


def seed_targets(settings: Settings, *, nickname: str = "listener_1") -> None:
    db_path = sqlite_path(settings)
    now = datetime.now(UTC)
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO devices
                (user_id, device_id, caption, device_type, created_at, updated_at)
            SELECT id, ?, ?, ?, ?, ? FROM users WHERE nickname = ?
            """,
            ("phone-01", "Phone", "mobile", now.isoformat(), now.isoformat(), nickname),
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
        connection.commit()


def test_save_then_read_settings_across_all_scopes(
    client: TestClient, settings: Settings
) -> None:
    register_user(client)
    seed_targets(settings)

    account = client.post(
        "/api/2/settings/listener_1/account.json",
        auth=("listener_1", "supersecret"),
        json={"set": {"public_profile": False}, "remove": []},
    )
    device = client.post(
        "/api/2/settings/listener_1/device.json?device=phone-01",
        auth=("listener_1", "supersecret"),
        json={"set": {"playback_speed": 1.25}, "remove": []},
    )
    podcast = client.post(
        "/api/2/settings/listener_1/podcast.json?podcast=https://example.com/feed.xml",
        auth=("listener_1", "supersecret"),
        json={"set": {"public_subscription": False}, "remove": []},
    )
    episode = client.post(
        "/api/2/settings/listener_1/episode.json?podcast=https://example.com/feed.xml&episode=https://example.com/episode-1.mp3",
        auth=("listener_1", "supersecret"),
        json={"set": {"is_favorite": True}, "remove": []},
    )

    read_back = {
        "account": client.get(
            "/api/2/settings/listener_1/account.json",
            auth=("listener_1", "supersecret"),
        ),
        "device": client.get(
            "/api/2/settings/listener_1/device.json?device=phone-01",
            auth=("listener_1", "supersecret"),
        ),
        "podcast": client.get(
            "/api/2/settings/listener_1/podcast.json?podcast=https://example.com/feed.xml",
            auth=("listener_1", "supersecret"),
        ),
        "episode": client.get(
            "/api/2/settings/listener_1/episode.json?podcast=https://example.com/feed.xml&episode=https://example.com/episode-1.mp3",
            auth=("listener_1", "supersecret"),
        ),
    }

    assert account.status_code == 200
    assert device.status_code == 200
    assert podcast.status_code == 200
    assert episode.status_code == 200
    assert read_back["account"].json() == {"public_profile": False}
    assert read_back["device"].json() == {"playback_speed": 1.25}
    assert read_back["podcast"].json() == {"public_subscription": False}
    assert read_back["episode"].json() == {"is_favorite": True}


def test_settings_flow_supports_nested_json_and_removals(
    client: TestClient, settings: Settings
) -> None:
    register_user(client)
    seed_targets(settings)

    created = client.post(
        "/api/2/settings/listener_1/account.json",
        auth=("listener_1", "supersecret"),
        json={
            "set": {
                "store_user_agent": True,
                "custom": {"bookmarks": [1, 2], "enabled": True, "value": None},
            },
            "remove": [],
        },
    )
    removed = client.post(
        "/api/2/settings/listener_1/account.json",
        auth=("listener_1", "supersecret"),
        json={"set": {}, "remove": ["store_user_agent"]},
    )

    assert created.status_code == 200
    assert created.json()["custom"] == {
        "bookmarks": [1, 2],
        "enabled": True,
        "value": None,
    }
    assert removed.status_code == 200
    assert removed.json() == {
        "custom": {"bookmarks": [1, 2], "enabled": True, "value": None}
    }


def test_settings_flow_rejects_cross_account_and_missing_query_params(
    client: TestClient, settings: Settings
) -> None:
    register_user(client)
    register_user(client, nickname="listener_2")
    seed_targets(settings)

    denied = client.post(
        "/api/2/settings/listener_1/account.json",
        auth=("listener_2", "supersecret"),
        json={"set": {"public_profile": False}, "remove": []},
    )
    missing = client.get(
        "/api/2/settings/listener_1/episode.json?podcast=https://example.com/feed.xml",
        auth=("listener_1", "supersecret"),
    )

    assert denied.status_code == 403
    assert missing.status_code == 400


def test_settings_flow_returns_not_found_for_mismatched_episode_scope(
    client: TestClient, settings: Settings
) -> None:
    register_user(client)
    seed_targets(settings)

    response = client.get(
        "/api/2/settings/listener_1/episode.json?podcast=https://example.com/other.xml&episode=https://example.com/episode-1.mp3",
        auth=("listener_1", "supersecret"),
    )

    assert response.status_code == 404
