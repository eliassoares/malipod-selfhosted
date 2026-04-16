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


def seed_update_scenario(settings: Settings) -> int:
    db_path = sqlite_path(settings)
    now = datetime.now(UTC)
    later = now + timedelta(minutes=5)
    latest = later + timedelta(minutes=5)

    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO devices (
                user_id, device_id, caption, device_type, created_at, updated_at
            )
            SELECT id, ?, ?, ?, ?, ? FROM users WHERE nickname = ?
            """,
            (
                "sync-box",
                "Sync Box",
                "server",
                now.isoformat(),
                latest.isoformat(),
                "listener_1",
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
                "https://example.com/feed-current.xml",
                "Current Feed",
                "Current description",
                "https://example.com/feed",
                "https://example.com/feed.png",
                "https://example.com/malipod/current",
                now.isoformat(),
                latest.isoformat(),
            ),
        )
        cursor.execute(
            """
            INSERT INTO device_subscriptions
                (device_pk, feed_id, subscribed_at, unsubscribed_at, updated_at)
            SELECT devices.id, podcast_feeds.id, ?, NULL, ?
            FROM devices, podcast_feeds
            WHERE devices.device_id = ? AND podcast_feeds.feed_url = ?
            """,
            (
                now.isoformat(),
                later.isoformat(),
                "sync-box",
                "https://example.com/feed-current.xml",
            ),
        )
        cursor.execute(
            """
            INSERT INTO episodes
                (
                    feed_id, episode_url, title, description, website,
                    mygpo_link, released_at, created_at, updated_at
                )
            SELECT id, ?, ?, ?, ?, ?, ?, ?, ? FROM podcast_feeds WHERE feed_url = ?
            """,
            (
                "https://example.com/episode-1.mp3",
                "Episode One",
                "Episode description",
                "https://example.com/episode-1",
                "https://example.com/malipod/episode-1",
                now.isoformat(),
                now.isoformat(),
                latest.isoformat(),
                "https://example.com/feed-current.xml",
            ),
        )
        cursor.execute(
            """
            INSERT INTO episode_actions
                (
                    user_id, device_pk, episode_id, status, action, occurred_at,
                    updated_at
                )
            SELECT users.id, devices.id, episodes.id, ?, ?, ?, ?
            FROM users, devices, episodes
            WHERE users.nickname = ?
              AND devices.device_id = ?
              AND episodes.episode_url = ?
            """,
            (
                "download",
                '{"downloaded": true}',
                latest.isoformat(),
                latest.isoformat(),
                "listener_1",
                "sync-box",
                "https://example.com/episode-1.mp3",
            ),
        )
        connection.commit()
    return int(later.timestamp())


def test_device_create_and_partial_update_flow(client: TestClient) -> None:
    register_user(client)

    created = client.post(
        "/api/2/devices/listener_1/workstation-1.json",
        auth=("listener_1", "supersecret"),
        json={"caption": "Desk Machine", "type": "desktop"},
    )
    assert created.status_code == 200

    updated = client.post(
        "/api/2/devices/listener_1/workstation-1.json",
        auth=("listener_1", "supersecret"),
        json={"caption": "Renamed Machine"},
    )
    assert updated.status_code == 200

    devices = client.get(
        "/api/2/devices/listener_1.json",
        auth=("listener_1", "supersecret"),
    )
    device = next(d for d in devices.json() if d["id"] == "workstation-1")
    assert device["caption"] == "Renamed Machine"
    assert device["type"] == "desktop"


def test_device_list_returns_empty_array_for_user_without_devices(
    client: TestClient,
) -> None:
    register_user(client)

    response = client.get(
        "/api/2/devices/listener_1.json",
        auth=("listener_1", "supersecret"),
    )

    assert response.status_code == 200
    assert response.json() == []


def test_updates_endpoint_filters_by_since_and_includes_actions(
    client: TestClient, settings: Settings
) -> None:
    register_user(client)
    since = seed_update_scenario(settings)

    response = client.get(
        f"/api/2/updates/listener_1/sync-box.json?since={since}&include_actions=true",
        auth=("listener_1", "supersecret"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["add"] == []
    assert payload["remove"] == []
    assert len(payload["updates"]) == 1
    assert payload["updates"][0]["status"] == "download"
    assert payload["updates"][0]["action"] == {"downloaded": True}


def test_updates_endpoint_rejects_unknown_device(client: TestClient) -> None:
    register_user(client)

    response = client.get(
        "/api/2/updates/listener_1/missing-device.json",
        auth=("listener_1", "supersecret"),
    )

    assert response.status_code == 404


def test_updates_endpoint_includes_projection_from_episodes_api_upload(
    client: TestClient,
) -> None:
    register_user(client)

    create_device = client.post(
        "/api/2/devices/listener_1/sync-box.json",
        auth=("listener_1", "supersecret"),
        json={"caption": "Sync Box", "type": "server"},
    )
    uploaded = client.post(
        "/api/2/episodes/listener_1.json",
        auth=("listener_1", "supersecret"),
        json=[
            {
                "podcast": "https://example.com/feed-current.xml",
                "episode": "https://example.com/episode-1.mp3",
                "device": "sync-box",
                "action": "download",
            }
        ],
    )
    since = uploaded.json()["timestamp"] - 1
    updates = client.get(
        f"/api/2/updates/listener_1/sync-box.json?since={since}&include_actions=true",
        auth=("listener_1", "supersecret"),
    )

    assert create_device.status_code == 200
    assert uploaded.status_code == 200
    assert updates.status_code == 200
    assert len(updates.json()["updates"]) == 1
    assert updates.json()["updates"][0]["status"] == "download"
    assert updates.json()["updates"][0]["action"] == {}
