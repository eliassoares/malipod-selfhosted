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
    assert count_rows(settings, "users") == 0
