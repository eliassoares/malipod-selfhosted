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


def seed_subscription_state(
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
                nickname,
            ),
        )
        cursor.execute(
            """
            INSERT INTO devices (
                user_id, device_id, caption, device_type, created_at, updated_at
            )
            SELECT id, ?, ?, ?, ?, ? FROM users WHERE nickname = ?
            """,
            (
                "tablet-01",
                "My Tablet",
                "mobile",
                now.isoformat(),
                now.isoformat(),
                nickname,
            ),
        )
        for feed_url, title in [
            ("https://example.com/feed-a.xml", "Feed A"),
            ("https://example.com/feed-b.xml", "Feed B"),
            ("https://example.com/feed-c.xml", "Feed C"),
        ]:
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
                    feed_url,
                    title,
                    None,
                    None,
                    None,
                    None,
                    now.isoformat(),
                    now.isoformat(),
                ),
            )
        for device_id, feed_url in [
            ("phone-01", "https://example.com/feed-a.xml"),
            ("phone-01", "https://example.com/feed-b.xml"),
            ("tablet-01", "https://example.com/feed-b.xml"),
            ("tablet-01", "https://example.com/feed-c.xml"),
        ]:
            cursor.execute(
                """
                INSERT INTO device_subscriptions
                    (device_pk, feed_id, subscribed_at, unsubscribed_at, updated_at)
                SELECT devices.id, podcast_feeds.id, ?, NULL, ?
                FROM devices, podcast_feeds
                WHERE devices.device_id = ? AND podcast_feeds.feed_url = ?
                """,
                (now.isoformat(), now.isoformat(), device_id, feed_url),
            )
        connection.commit()


def set_user_centralize_sync(
    settings: Settings, *, nickname: str, enabled: bool
) -> None:
    db_path = sqlite_path(settings)
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE users SET centralize_sync = ? WHERE nickname = ?",
            (1 if enabled else 0, nickname),
        )
        connection.commit()


def test_get_device_subscriptions_contract_json_and_jsonp(
    client: TestClient, settings: Settings
) -> None:
    register_user(client)
    seed_subscription_state(settings)

    response = client.get(
        "/subscriptions/listener_1/phone-01.json",
        auth=("listener_1", "supersecret"),
    )
    jsonp = client.get(
        "/subscriptions/listener_1/phone-01.json?jsonp=callback",
        auth=("listener_1", "supersecret"),
    )

    assert response.status_code == 200
    assert [item["url"] for item in response.json()] == [
        "https://example.com/feed-a.xml",
        "https://example.com/feed-b.xml",
    ]
    assert jsonp.status_code == 200
    assert jsonp.text.startswith("callback([")


def test_get_device_subscriptions_contract_supports_centralized_union(
    client: TestClient,
    settings: Settings,
) -> None:
    register_user(client)
    seed_subscription_state(settings)

    device_scoped = client.get(
        "/subscriptions/listener_1/phone-01.json",
        auth=("listener_1", "supersecret"),
    )
    set_user_centralize_sync(settings, nickname="listener_1", enabled=True)
    centralized = client.get(
        "/subscriptions/listener_1/phone-01.json",
        auth=("listener_1", "supersecret"),
    )

    assert device_scoped.status_code == 200
    assert [item["url"] for item in device_scoped.json()] == [
        "https://example.com/feed-a.xml",
        "https://example.com/feed-b.xml",
    ]
    assert centralized.status_code == 200
    assert [item["url"] for item in centralized.json()] == [
        "https://example.com/feed-a.xml",
        "https://example.com/feed-b.xml",
        "https://example.com/feed-c.xml",
    ]


def test_get_device_subscriptions_contract_opml_honors_centralize_sync(
    client: TestClient,
    settings: Settings,
) -> None:
    register_user(client)
    seed_subscription_state(settings)

    device_scoped = client.get(
        "/subscriptions/listener_1/phone-01.opml",
        auth=("listener_1", "supersecret"),
    )
    set_user_centralize_sync(settings, nickname="listener_1", enabled=True)
    centralized = client.get(
        "/subscriptions/listener_1/phone-01.opml",
        auth=("listener_1", "supersecret"),
    )

    assert device_scoped.status_code == 200
    assert "https://example.com/feed-a.xml" in device_scoped.text
    assert "https://example.com/feed-c.xml" not in device_scoped.text
    assert centralized.status_code == 200
    assert "https://example.com/feed-a.xml" in centralized.text
    assert "https://example.com/feed-c.xml" in centralized.text


def test_get_device_subscriptions_contract_txt_honors_centralize_sync(
    client: TestClient,
    settings: Settings,
) -> None:
    register_user(client)
    seed_subscription_state(settings)

    device_scoped = client.get(
        "/subscriptions/listener_1/phone-01.txt",
        auth=("listener_1", "supersecret"),
    )
    set_user_centralize_sync(settings, nickname="listener_1", enabled=True)
    centralized = client.get(
        "/subscriptions/listener_1/phone-01.txt",
        auth=("listener_1", "supersecret"),
    )

    assert device_scoped.status_code == 200
    assert "https://example.com/feed-a.xml" in device_scoped.text
    assert "https://example.com/feed-c.xml" not in device_scoped.text
    assert centralized.status_code == 200
    assert "https://example.com/feed-a.xml" in centralized.text
    assert "https://example.com/feed-c.xml" in centralized.text


def test_get_account_subscriptions_contract_opml_and_txt(
    client: TestClient, settings: Settings
) -> None:
    register_user(client)
    seed_subscription_state(settings)

    opml = client.get(
        "/subscriptions/listener_1.opml",
        auth=("listener_1", "supersecret"),
    )
    txt = client.get(
        "/subscriptions/listener_1.txt",
        auth=("listener_1", "supersecret"),
    )

    assert opml.status_code == 200
    assert "https://example.com/feed-c.xml" in opml.text
    assert txt.status_code == 200
    assert txt.text.splitlines() == [
        "https://example.com/feed-a.xml",
        "https://example.com/feed-b.xml",
        "https://example.com/feed-c.xml",
    ]


def test_get_subscriptions_contract_rejects_invalid_format_and_unknown_device(
    client: TestClient, settings: Settings
) -> None:
    register_user(client)
    seed_subscription_state(settings)

    invalid_format = client.get(
        "/subscriptions/listener_1/phone-01.xml",
        auth=("listener_1", "supersecret"),
    )
    missing_device = client.get(
        "/subscriptions/listener_1/missing.json",
        auth=("listener_1", "supersecret"),
    )

    assert invalid_format.status_code == 400
    assert missing_device.status_code == 404


def test_put_device_subscriptions_contract_returns_empty_body_and_creates_device(
    client: TestClient,
) -> None:
    register_user(client)

    response = client.put(
        "/subscriptions/listener_1/new-device.txt",
        auth=("listener_1", "supersecret"),
        content="https://example.com/feed-a.xml\nhttps://example.com/feed-b.xml\n",
        headers={"Content-Type": "text/plain"},
    )
    device_read = client.get(
        "/subscriptions/listener_1/new-device.json",
        auth=("listener_1", "supersecret"),
    )

    assert response.status_code == 200
    assert response.content == b""
    assert [item["url"] for item in device_read.json()] == [
        "https://example.com/feed-a.xml",
        "https://example.com/feed-b.xml",
    ]


def test_subscription_delta_contract_reports_timestamp_and_update_urls(
    client: TestClient, settings: Settings
) -> None:
    register_user(client)
    seed_subscription_state(settings)

    response = client.post(
        "/api/2/subscriptions/listener_1/phone-01.json",
        auth=("listener_1", "supersecret"),
        json={
            "add": [" http://example.com/new.xml ", "ftp://invalid.example/feed"],
            "remove": ["https://example.com/feed-a.xml"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["timestamp"] >= 1
    assert payload["update_urls"] == [
        [" http://example.com/new.xml ", "http://example.com/new.xml"],
        ["ftp://invalid.example/feed", ""],
    ]


def test_subscription_delta_contract_rejects_conflicting_url(
    client: TestClient,
    settings: Settings,
) -> None:
    register_user(client)
    seed_subscription_state(settings)

    response = client.post(
        "/api/2/subscriptions/listener_1/phone-01.json",
        auth=("listener_1", "supersecret"),
        json={
            "add": ["https://example.com/feed-a.xml"],
            "remove": ["https://example.com/feed-a.xml"],
        },
    )

    assert response.status_code == 400


def test_get_subscription_changes_contract_returns_changes_since_timestamp(
    client: TestClient, settings: Settings
) -> None:
    register_user(client)
    seed_subscription_state(settings)
    baseline = client.get(
        "/api/2/subscriptions/listener_1/phone-01.json?since=0",
        auth=("listener_1", "supersecret"),
    )
    delta = client.post(
        "/api/2/subscriptions/listener_1/phone-01.json",
        auth=("listener_1", "supersecret"),
        json={
            "add": ["https://example.com/feed-d.xml"],
            "remove": ["https://example.com/feed-a.xml"],
        },
    )
    changes = client.get(
        f"/api/2/subscriptions/listener_1/phone-01.json?since={baseline.json()['timestamp']}",
        auth=("listener_1", "supersecret"),
    )
    empty = client.get(
        f"/api/2/subscriptions/listener_1/phone-01.json?since={delta.json()['timestamp']}",
        auth=("listener_1", "supersecret"),
    )

    assert changes.status_code == 200
    assert changes.json()["add"] == ["https://example.com/feed-d.xml"]
    assert changes.json()["remove"] == ["https://example.com/feed-a.xml"]
    assert empty.status_code == 200
    assert empty.json()["add"] == []
    assert empty.json()["remove"] == []


def test_get_subscription_changes_contract_centralized_add_is_union_across_devices(
    client: TestClient,
    settings: Settings,
) -> None:
    register_user(client)
    seed_subscription_state(settings)
    set_user_centralize_sync(settings, nickname="listener_1", enabled=True)

    baseline = client.get(
        "/api/2/subscriptions/listener_1/phone-01.json?since=0",
        auth=("listener_1", "supersecret"),
    )
    client.post(
        "/api/2/subscriptions/listener_1/phone-01.json",
        auth=("listener_1", "supersecret"),
        json={"add": ["https://example.com/feed-d.xml"], "remove": []},
    )
    client.post(
        "/api/2/subscriptions/listener_1/tablet-01.json",
        auth=("listener_1", "supersecret"),
        json={"add": ["https://example.com/feed-e.xml"], "remove": []},
    )
    changes = client.get(
        f"/api/2/subscriptions/listener_1/phone-01.json?since={baseline.json()['timestamp']}",
        auth=("listener_1", "supersecret"),
    )

    assert changes.status_code == 200
    assert set(changes.json()["add"]) == {
        "https://example.com/feed-d.xml",
        "https://example.com/feed-e.xml",
    }


def test_get_subscription_changes_contract_centralized_remove_only_when_absent(
    client: TestClient,
    settings: Settings,
) -> None:
    register_user(client)
    seed_subscription_state(settings)
    set_user_centralize_sync(settings, nickname="listener_1", enabled=True)

    baseline = client.get(
        "/api/2/subscriptions/listener_1/phone-01.json?since=0",
        auth=("listener_1", "supersecret"),
    )
    client.post(
        "/api/2/subscriptions/listener_1/phone-01.json",
        auth=("listener_1", "supersecret"),
        json={"add": [], "remove": ["https://example.com/feed-b.xml"]},
    )
    changes_while_still_subscribed = client.get(
        f"/api/2/subscriptions/listener_1/phone-01.json?since={baseline.json()['timestamp']}",
        auth=("listener_1", "supersecret"),
    )
    since_all_devices = changes_while_still_subscribed.json()["timestamp"]

    client.post(
        "/api/2/subscriptions/listener_1/tablet-01.json",
        auth=("listener_1", "supersecret"),
        json={"add": [], "remove": ["https://example.com/feed-b.xml"]},
    )
    changes_after_removed_everywhere = client.get(
        f"/api/2/subscriptions/listener_1/phone-01.json?since={since_all_devices}",
        auth=("listener_1", "supersecret"),
    )

    assert changes_while_still_subscribed.status_code == 200
    assert changes_while_still_subscribed.json()["remove"] == []
    assert changes_after_removed_everywhere.status_code == 200
    assert changes_after_removed_everywhere.json()["remove"] == [
        "https://example.com/feed-b.xml"
    ]
