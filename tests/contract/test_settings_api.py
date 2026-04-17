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


def seed_settings_targets(
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
        cursor.execute(
            """
            INSERT INTO account_settings
                (user_id, settings, created_at, updated_at)
            SELECT id, ?, ?, ? FROM users WHERE nickname = ?
            """,
            ('{"public_profile": false}', now.isoformat(), now.isoformat(), nickname),
        )
        cursor.execute(
            """
            INSERT INTO device_settings
                (user_id, device_pk, settings, created_at, updated_at)
            SELECT users.id, devices.id, ?, ?, ?
            FROM users JOIN devices ON devices.user_id = users.id
            WHERE users.nickname = ? AND devices.device_id = ?
            """,
            (
                '{"playback_speed": 1.25}',
                now.isoformat(),
                now.isoformat(),
                nickname,
                "phone-01",
            ),
        )
        cursor.execute(
            """
            INSERT INTO podcast_settings
                (user_id, feed_id, settings, created_at, updated_at)
            SELECT users.id, podcast_feeds.id, ?, ?, ?
            FROM users, podcast_feeds
            WHERE users.nickname = ? AND podcast_feeds.feed_url = ?
            """,
            (
                '{"public_subscription": false}',
                now.isoformat(),
                now.isoformat(),
                nickname,
                "https://example.com/feed.xml",
            ),
        )
        cursor.execute(
            """
            INSERT INTO episode_settings
                (user_id, episode_id, settings, created_at, updated_at)
            SELECT users.id, episodes.id, ?, ?, ?
            FROM users, episodes
            WHERE users.nickname = ? AND episodes.episode_url = ?
            """,
            (
                '{"is_favorite": true}',
                now.isoformat(),
                now.isoformat(),
                nickname,
                "https://example.com/episode-1.mp3",
            ),
        )
        connection.commit()


def test_get_settings_contract_returns_scoped_documents(
    client: TestClient, settings: Settings
) -> None:
    register_user(client)
    seed_settings_targets(settings)

    account = client.get(
        "/api/2/settings/listener_1/account.json",
        auth=("listener_1", "supersecret"),
    )
    device = client.get(
        "/api/2/settings/listener_1/device.json?device=phone-01",
        auth=("listener_1", "supersecret"),
    )
    podcast = client.get(
        "/api/2/settings/listener_1/podcast.json?podcast=https://example.com/feed.xml",
        auth=("listener_1", "supersecret"),
    )
    episode = client.get(
        "/api/2/settings/listener_1/episode.json?podcast=https://example.com/feed.xml&episode=https://example.com/episode-1.mp3",
        auth=("listener_1", "supersecret"),
    )

    assert account.status_code == 200
    assert account.json() == {"public_profile": False}
    assert device.status_code == 200
    assert device.json() == {"playback_speed": 1.25}
    assert podcast.status_code == 200
    assert podcast.json() == {"public_subscription": False}
    assert episode.status_code == 200
    assert episode.json() == {"is_favorite": True}


def test_get_settings_contract_returns_empty_object_for_valid_empty_scope(
    client: TestClient, settings: Settings
) -> None:
    register_user(client)
    seed_settings_targets(settings)

    response = client.get(
        "/api/2/settings/listener_1/device.json?device=phone-01",
        auth=("listener_1", "supersecret"),
    )

    assert response.status_code == 200


def test_get_settings_contract_rejects_missing_params_and_foreign_user(
    client: TestClient, settings: Settings
) -> None:
    register_user(client)
    register_user(client, nickname="listener_2")
    seed_settings_targets(settings)

    missing = client.get(
        "/api/2/settings/listener_1/device.json",
        auth=("listener_1", "supersecret"),
    )
    denied = client.get(
        "/api/2/settings/listener_1/account.json",
        auth=("listener_2", "supersecret"),
    )
    unauthorized = client.get("/api/2/settings/listener_1/account.json")

    assert missing.status_code == 400
    assert denied.status_code == 403
    assert unauthorized.status_code == 401


def test_post_settings_contract_updates_and_removes_keys(
    client: TestClient, settings: Settings
) -> None:
    register_user(client)
    seed_settings_targets(settings)

    response = client.post(
        "/api/2/settings/listener_1/account.json",
        auth=("listener_1", "supersecret"),
        json={
            "set": {"store_user_agent": True},
            "remove": ["public_profile"],
        },
    )

    assert response.status_code == 200
    assert response.json() == {"store_user_agent": True}


def test_post_settings_contract_rejects_bad_payload_and_missing_targets(
    client: TestClient, settings: Settings
) -> None:
    register_user(client)
    seed_settings_targets(settings)

    invalid = client.post(
        "/api/2/settings/listener_1/account.json",
        auth=("listener_1", "supersecret"),
        content='{"set": []}',
        headers={"Content-Type": "application/json"},
    )
    missing_target = client.post(
        "/api/2/settings/listener_1/device.json?device=missing-device",
        auth=("listener_1", "supersecret"),
        json={"set": {"caption": "new"}, "remove": []},
    )

    assert invalid.status_code == 400
    assert missing_target.status_code == 404
