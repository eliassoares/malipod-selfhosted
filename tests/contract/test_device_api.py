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


def get_sqlite_path(settings: Settings) -> Path:
    return Path(settings.test_database_url.removeprefix("sqlite+aiosqlite:///"))


def seed_device_subscription_data(settings: Settings) -> None:
    db_path = get_sqlite_path(settings)
    now = datetime.now(UTC)
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
                "phone-01",
                "My Phone",
                "mobile",
                now.isoformat(),
                now.isoformat(),
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
                "https://example.com/feed.xml",
                "My Feed",
                "Description",
                "https://example.com",
                "https://example.com/logo.png",
                "https://example.com/malipod/feed",
                now.isoformat(),
                now.isoformat(),
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
                now.isoformat(),
                "phone-01",
                "https://example.com/feed.xml",
            ),
        )
        connection.commit()


def seed_device_update_data(settings: Settings) -> None:
    db_path = get_sqlite_path(settings)
    now = datetime.now(UTC)
    later = now + timedelta(minutes=5)
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
                now.isoformat(),
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
                later.isoformat(),
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
                now.isoformat(),
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
                later.isoformat(),
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
                "play",
                '{"position": 120, "started": true}',
                later.isoformat(),
                later.isoformat(),
                "listener_1",
                "sync-box",
                "https://example.com/episode-1.mp3",
            ),
        )
        connection.commit()


def test_device_upsert_contract(client: TestClient) -> None:
    """POST upsert returns empty 200 per gpodder spec."""
    register_user(client)

    response = client.post(
        "/api/2/devices/listener_1/workstation-1.json",
        auth=("listener_1", "supersecret"),
        json={"caption": "Desk Machine", "type": "desktop"},
    )

    assert response.status_code == 200
    assert response.content == b""


def test_device_upsert_empty_body_creates_device(client: TestClient) -> None:
    """The spec allows empty body — device is created with defaults."""
    register_user(client)

    response = client.post(
        "/api/2/devices/listener_1/my-phone.json",
        auth=("listener_1", "supersecret"),
        json={},
    )
    assert response.status_code == 200

    devices = client.get(
        "/api/2/devices/listener_1.json",
        auth=("listener_1", "supersecret"),
    )
    device_ids = [d["id"] for d in devices.json()]
    assert "my-phone" in device_ids


def test_device_upsert_requires_valid_device_id(client: TestClient) -> None:
    register_user(client)

    response = client.post(
        "/api/2/devices/listener_1/bad id.json",
        auth=("listener_1", "supersecret"),
        json={"caption": "Broken", "type": "desktop"},
    )

    assert response.status_code == 400
    assert "device_id" in response.json()["detail"]


def test_device_upsert_rejects_different_authenticated_user(client: TestClient) -> None:
    register_user(client)
    register_user(client, nickname="listener_2")

    response = client.post(
        "/api/2/devices/listener_1/workstation-1.json",
        auth=("listener_2", "supersecret"),
        json={"caption": "Desk Machine", "type": "desktop"},
    )

    assert response.status_code == 403


def test_device_list_contract(client: TestClient, settings: Settings) -> None:
    register_user(client)
    seed_device_subscription_data(settings)

    response = client.get(
        "/api/2/devices/listener_1.json",
        auth=("listener_1", "supersecret"),
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "phone-01",
            "caption": "My Phone",
            "type": "mobile",
            "subscriptions": 1,
        }
    ]


def test_device_updates_contract(client: TestClient, settings: Settings) -> None:
    register_user(client)
    seed_device_update_data(settings)

    response = client.get(
        "/api/2/updates/listener_1/sync-box.json?include_actions=true",
        auth=("listener_1", "supersecret"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["add"][0]["title"] == "Current Feed"
    assert payload["updates"][0]["status"] == "play"
    assert payload["updates"][0]["action"] == {"position": 120, "started": True}
    assert isinstance(payload["timestamp"], int)
