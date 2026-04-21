from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

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


def api_login(client: TestClient, nickname: str = "listener_1") -> None:
    response = client.post(
        f"/api/2/auth/{nickname}/login.json",
        auth=(nickname, "supersecret"),
    )
    assert response.status_code == 200
    assert "sessionid" in client.cookies


def sqlite_path(settings: Settings) -> Path:
    return Path(settings.test_database_url.removeprefix("sqlite+aiosqlite:///"))


def get_user_id(settings: Settings, nickname: str) -> int:
    db_path = sqlite_path(settings)
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM users WHERE nickname = ?", (nickname,))
        row = cursor.fetchone()
        assert row is not None
        return int(row[0])


def upsert_account_settings(
    settings: Settings, nickname: str, *, data: dict[str, Any], updated_at: datetime
) -> None:
    db_path = sqlite_path(settings)
    user_id = get_user_id(settings, nickname)
    now = datetime.now(UTC)
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO account_settings (user_id, settings, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE
            SET settings=excluded.settings,
                updated_at=excluded.updated_at
            """,
            (user_id, json.dumps(data), now.isoformat(), updated_at.isoformat()),
        )
        connection.commit()


def read_account_settings(settings: Settings, nickname: str) -> dict[str, Any]:
    db_path = sqlite_path(settings)
    user_id = get_user_id(settings, nickname)
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT settings FROM account_settings WHERE user_id = ?", (user_id,)
        )
        row = cursor.fetchone()
        assert row is not None
        return cast("dict[str, Any]", json.loads(row[0]))


def seed_device(settings: Settings, nickname: str) -> None:
    db_path = sqlite_path(settings)
    user_id = get_user_id(settings, nickname)
    now = datetime.now(UTC)
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO devices
                (user_id, device_id, caption, device_type, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, "phone-01", "Phone", "mobile", now.isoformat(), now.isoformat()),
        )
        connection.commit()


def count_rows(settings: Settings, table: str) -> int:
    db_path = sqlite_path(settings)
    queries = {
        "users": "SELECT COUNT(*) FROM users",
        "devices": "SELECT COUNT(*) FROM devices",
        "account_settings": "SELECT COUNT(*) FROM account_settings",
    }
    query = queries.get(table)
    if query is None:
        raise ValueError("unsupported table")
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(query)
        return int(cursor.fetchone()[0])


def test_profile_page_requires_login(client: TestClient) -> None:
    response = client.get("/user/profile/listener_1", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_profile_page_shows_user_data_tools_when_logged_in(client: TestClient) -> None:
    register_user(client)
    api_login(client)

    response = client.get("/user/profile/listener_1")
    assert response.status_code == 200
    html = response.text
    assert 'action="/user/profile/listener_1/export"' in html
    assert 'action="/user/profile/listener_1/import"' in html
    assert 'action="/user/profile/listener_1/delete-data"' in html
    assert 'action="/user/profile/listener_1/delete-user"' in html
    assert 'name="snapshot_file"' in html


def test_export_returns_attachment_and_excludes_password_and_sessions(
    client: TestClient,
) -> None:
    register_user(client)
    api_login(client)

    response = client.post("/user/profile/listener_1/export", follow_redirects=False)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    disposition = response.headers.get("content-disposition", "")
    assert disposition.startswith('attachment; filename="malipod_data_')
    assert disposition.endswith('.json"')

    snapshot = response.json()
    assert "authenticated_sessions" not in snapshot
    assert snapshot["users"][0]["email"] == "listener_1@example.com"
    assert "password_hash" not in snapshot["users"][0]
    assert "password_salt" not in snapshot["users"][0]


def test_import_updates_newer_account_settings(
    client: TestClient,
    settings: Settings,
) -> None:
    register_user(client)
    api_login(client)

    old_updated_at = datetime.now(UTC) - timedelta(days=1)
    upsert_account_settings(
        settings,
        "listener_1",
        data={"public_profile": False},
        updated_at=old_updated_at,
    )

    export = client.post("/user/profile/listener_1/export").json()
    new_updated_at = datetime.now(UTC) + timedelta(days=1)
    export["account_settings"] = [
        {
            "settings": {"public_profile": True},
            "created_at": old_updated_at.isoformat(),
            "updated_at": new_updated_at.isoformat(),
        }
    ]

    response = client.post(
        "/user/profile/listener_1/import",
        files={
            "snapshot_file": (
                "snapshot.json",
                json.dumps(export),
                "application/json",
            )
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/user/profile/listener_1"
    assert read_account_settings(settings, "listener_1")["public_profile"] is True


def test_delete_data_removes_related_rows_but_keeps_user(
    client: TestClient,
    settings: Settings,
) -> None:
    register_user(client)
    api_login(client)
    seed_device(settings, "listener_1")
    upsert_account_settings(
        settings,
        "listener_1",
        data={"public_profile": False},
        updated_at=datetime.now(UTC),
    )

    assert count_rows(settings, "users") == 1
    assert count_rows(settings, "devices") == 1
    assert count_rows(settings, "account_settings") == 1

    response = client.post(
        "/user/profile/listener_1/delete-data",
        data={"confirm": "DELETE"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/login"
    assert "set-cookie" in response.headers

    assert count_rows(settings, "users") == 1
    assert count_rows(settings, "devices") == 0
    assert count_rows(settings, "account_settings") == 0


def test_delete_user_removes_user_and_redirects_home(
    client: TestClient,
    settings: Settings,
) -> None:
    register_user(client)
    api_login(client)

    response = client.post(
        "/user/profile/listener_1/delete-user",
        data={"confirm": "DELETE"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"
    assert "set-cookie" in response.headers
    assert count_rows(settings, "users") == 0


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


def test_import_rejects_file_too_large(client: TestClient) -> None:
    register_user(client)
    api_login(client)
    big_data = b"x" * (10 * 1024 * 1024 + 2)
    response = client.post(
        "/user/profile/listener_1/import",
        files={"snapshot_file": ("big.json", big_data, "application/json")},
        follow_redirects=False,
    )
    assert response.status_code == 413


def test_import_rejects_invalid_json(client: TestClient) -> None:
    register_user(client)
    api_login(client)
    response = client.post(
        "/user/profile/listener_1/import",
        files={"snapshot_file": ("bad.json", b"not json {{{", "application/json")},
        follow_redirects=False,
    )
    assert response.status_code == 400


def test_import_rejects_snapshot_user_mismatch(client: TestClient) -> None:
    register_user(client)
    api_login(client)
    export = client.post("/user/profile/listener_1/export").json()
    export["users"][0]["email"] = "someone_else@example.com"
    response = client.post(
        "/user/profile/listener_1/import",
        files={
            "snapshot_file": (
                "snapshot.json",
                json.dumps(export).encode(),
                "application/json",
            )
        },
        follow_redirects=False,
    )
    assert response.status_code == 400


def test_import_rejects_invalid_feed_url(client: TestClient) -> None:
    register_user(client)
    api_login(client)
    export = client.post("/user/profile/listener_1/export").json()
    export["podcast_feeds"] = [
        {
            "feed_url": "not-a-valid-url",
            "title": "Bad Feed",
            "created_at": "2024-01-01T00:00:00+00:00",
            "updated_at": "2024-01-01T00:00:00+00:00",
        }
    ]
    response = client.post(
        "/user/profile/listener_1/import",
        files={
            "snapshot_file": (
                "snapshot.json",
                json.dumps(export).encode(),
                "application/json",
            )
        },
        follow_redirects=False,
    )
    assert response.status_code == 422


def test_delete_data_requires_confirm(client: TestClient) -> None:
    register_user(client)
    api_login(client)
    response = client.post(
        "/user/profile/listener_1/delete-data",
        data={"confirm": ""},
        follow_redirects=False,
    )
    assert response.status_code == 400


def test_delete_user_requires_confirm(client: TestClient) -> None:
    register_user(client)
    api_login(client)
    response = client.post(
        "/user/profile/listener_1/delete-user",
        data={"confirm": ""},
        follow_redirects=False,
    )
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Access control
# ---------------------------------------------------------------------------


def test_export_forbidden_for_other_user(client: TestClient) -> None:
    register_user(client, "listener_1")
    register_user(client, "listener_2")
    api_login(client, "listener_2")
    response = client.post("/user/profile/listener_1/export", follow_redirects=False)
    assert response.status_code == 404


def test_import_forbidden_for_other_user(client: TestClient) -> None:
    register_user(client, "listener_1")
    register_user(client, "listener_2")
    api_login(client, "listener_2")
    export: dict[str, list[object]] = {"users": [], "devices": []}
    response = client.post(
        "/user/profile/listener_1/import",
        files={
            "snapshot_file": (
                "snapshot.json",
                json.dumps(export).encode(),
                "application/json",
            )
        },
        follow_redirects=False,
    )
    assert response.status_code == 404


def test_delete_data_forbidden_for_other_user(client: TestClient) -> None:
    register_user(client, "listener_1")
    register_user(client, "listener_2")
    api_login(client, "listener_2")
    response = client.post(
        "/user/profile/listener_1/delete-data",
        data={"confirm": "DELETE"},
        follow_redirects=False,
    )
    assert response.status_code == 404


def test_delete_user_forbidden_for_other_user(client: TestClient) -> None:
    register_user(client, "listener_1")
    register_user(client, "listener_2")
    api_login(client, "listener_2")
    response = client.post(
        "/user/profile/listener_1/delete-user",
        data={"confirm": "DELETE"},
        follow_redirects=False,
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Merge logic
# ---------------------------------------------------------------------------


def test_import_ignores_older_account_settings(
    client: TestClient,
    settings: Settings,
) -> None:
    register_user(client)
    api_login(client)

    recent_updated_at = datetime.now(UTC)
    upsert_account_settings(
        settings,
        "listener_1",
        data={"theme": "dark"},
        updated_at=recent_updated_at,
    )

    export = client.post("/user/profile/listener_1/export").json()
    export["account_settings"] = [
        {
            "settings": {"theme": "light"},
            "created_at": (recent_updated_at - timedelta(days=2)).isoformat(),
            "updated_at": (recent_updated_at - timedelta(days=1)).isoformat(),
        }
    ]

    response = client.post(
        "/user/profile/listener_1/import",
        files={
            "snapshot_file": (
                "snapshot.json",
                json.dumps(export).encode(),
                "application/json",
            )
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert read_account_settings(settings, "listener_1")["theme"] == "dark"


# ---------------------------------------------------------------------------
# Delete-data broader table coverage
# ---------------------------------------------------------------------------


def test_delete_data_clears_device_subscriptions_and_events(
    client: TestClient,
    settings: Settings,
) -> None:
    register_user(client)
    api_login(client)

    now = datetime.now(UTC)
    snapshot: dict[str, Any] = {
        "users": [
            {
                "nickname": "listener_1",
                "email": "listener_1@example.com",
                "language_preference": "en",
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "accessed_at": now.isoformat(),
            }
        ],
        "devices": [
            {
                "device_id": "phone-01",
                "caption": "Phone",
                "device_type": "mobile",
                "sync_group": None,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            }
        ],
        "podcast_feeds": [
            {
                "feed_url": "https://example.com/feed.xml",
                "title": "Test Feed",
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            }
        ],
        "device_subscriptions": [
            {
                "device_id": "phone-01",
                "feed_url": "https://example.com/feed.xml",
                "subscribed_at": now.isoformat(),
                "updated_at": now.isoformat(),
            }
        ],
        "subscription_change_events": [
            {
                "device_id": "phone-01",
                "feed_url": "https://example.com/feed.xml",
                "operation": "subscribe",
                "created_at": now.isoformat(),
            }
        ],
    }
    import_response = client.post(
        "/user/profile/listener_1/import",
        files={
            "snapshot_file": (
                "snapshot.json",
                json.dumps(snapshot).encode(),
                "application/json",
            )
        },
        follow_redirects=False,
    )
    assert import_response.status_code == 303

    db_path = sqlite_path(settings)
    with sqlite3.connect(db_path) as conn:
        assert (
            conn.execute("SELECT COUNT(*) FROM device_subscriptions").fetchone()[0] == 1
        )
        assert (
            conn.execute("SELECT COUNT(*) FROM subscription_change_events").fetchone()[
                0
            ]
            == 1
        )

    client.post(
        "/user/profile/listener_1/delete-data",
        data={"confirm": "DELETE"},
        follow_redirects=False,
    )

    with sqlite3.connect(db_path) as conn:
        assert (
            conn.execute("SELECT COUNT(*) FROM device_subscriptions").fetchone()[0] == 0
        )
        assert (
            conn.execute("SELECT COUNT(*) FROM subscription_change_events").fetchone()[
                0
            ]
            == 0
        )
