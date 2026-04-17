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


def seed_list_state(
    settings: Settings,
    *,
    nickname: str = "listener_1",
) -> None:
    db_path = sqlite_path(settings)
    now = datetime.now(UTC)
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
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
                    f"https://example.com/{title.lower().replace(' ', '-')}",
                    None,
                    None,
                    now.isoformat(),
                    now.isoformat(),
                ),
            )
        cursor.execute(
            """
            INSERT INTO podcast_lists (user_id, title, name, created_at, updated_at)
            SELECT id, ?, ?, ?, ? FROM users WHERE nickname = ?
            """,
            (
                "My Python Podcasts",
                "my-python-podcasts",
                now.isoformat(),
                now.isoformat(),
                nickname,
            ),
        )
        for position, feed_url in enumerate(
            [
                "https://example.com/feed-a.xml",
                "https://example.com/feed-b.xml",
            ]
        ):
            cursor.execute(
                """
                INSERT INTO podcast_list_items
                    (list_id, feed_id, position, created_at, updated_at)
                SELECT podcast_lists.id, podcast_feeds.id, ?, ?, ?
                FROM podcast_lists, podcast_feeds
                WHERE podcast_lists.name = ? AND podcast_feeds.feed_url = ?
                """,
                (
                    position,
                    now.isoformat(),
                    now.isoformat(),
                    "my-python-podcasts",
                    feed_url,
                ),
            )
        connection.commit()


def test_get_user_podcast_lists_contract_returns_public_summaries(
    client: TestClient, settings: Settings
) -> None:
    register_user(client)
    seed_list_state(settings)

    response = client.get("/api/2/lists/listener_1.json")

    assert response.status_code == 200
    assert response.json() == [
        {
            "title": "My Python Podcasts",
            "name": "my-python-podcasts",
            "web": "http://localhost:8000/user/listener_1/lists/my-python-podcasts",
        }
    ]


def test_get_podcast_list_contract_renders_json_opml_and_txt(
    client: TestClient, settings: Settings
) -> None:
    register_user(client)
    seed_list_state(settings)

    as_json = client.get("/api/2/lists/listener_1/list/my-python-podcasts.json")
    as_opml = client.get("/api/2/lists/listener_1/list/my-python-podcasts.opml")
    as_txt = client.get("/api/2/lists/listener_1/list/my-python-podcasts.txt")

    assert as_json.status_code == 200
    assert as_json.json()["name"] == "my-python-podcasts"
    assert [item["url"] for item in as_json.json()["podcasts"]] == [
        "https://example.com/feed-a.xml",
        "https://example.com/feed-b.xml",
    ]
    assert as_opml.status_code == 200
    assert "https://example.com/feed-a.xml" in as_opml.text
    assert as_txt.status_code == 200
    assert as_txt.text.splitlines() == [
        "https://example.com/feed-a.xml",
        "https://example.com/feed-b.xml",
    ]


def test_get_podcast_list_contract_returns_not_found_for_missing_resources(
    client: TestClient, settings: Settings
) -> None:
    register_user(client)
    seed_list_state(settings)

    missing_user = client.get("/api/2/lists/missing_user.json")
    missing_list = client.get("/api/2/lists/listener_1/list/missing.json")

    assert missing_user.status_code == 404
    assert missing_list.status_code == 404


def test_create_podcast_list_contract_returns_303_and_conflict(
    client: TestClient,
) -> None:
    register_user(client)

    created = client.post(
        "/api/2/lists/listener_1/create.json?title=My%20Python%20Podcasts",
        auth=("listener_1", "supersecret"),
        json=["https://example.com/feed-a.xml", "https://example.com/feed-b.xml"],
        follow_redirects=False,
    )
    conflict = client.post(
        "/api/2/lists/listener_1/create.txt?title=My%20Python%20Podcasts",
        auth=("listener_1", "supersecret"),
        content="https://example.com/feed-c.xml\n",
        headers={"Content-Type": "text/plain"},
        follow_redirects=False,
    )

    assert created.status_code == 303
    assert (
        created.headers["location"]
        == "/api/2/lists/listener_1/list/my-python-podcasts.json"
    )
    assert conflict.status_code == 409


def test_update_and_delete_podcast_list_contract_require_owner_and_return_204(
    client: TestClient, settings: Settings
) -> None:
    register_user(client)
    register_user(client, nickname="listener_2")
    seed_list_state(settings)

    updated = client.put(
        "/api/2/lists/listener_1/list/my-python-podcasts.txt",
        auth=("listener_1", "supersecret"),
        content="https://example.com/feed-c.xml\n",
        headers={"Content-Type": "text/plain"},
    )
    denied = client.delete(
        "/api/2/lists/listener_1/list/my-python-podcasts.json",
        auth=("listener_2", "supersecret"),
    )
    deleted = client.delete(
        "/api/2/lists/listener_1/list/my-python-podcasts.json",
        auth=("listener_1", "supersecret"),
    )

    assert updated.status_code == 204
    assert denied.status_code == 403
    assert deleted.status_code == 204


def test_create_podcast_list_with_empty_body(client: TestClient) -> None:
    register_user(client)

    response = client.post(
        "/api/2/lists/listener_1/create.txt?title=Empty%20List",
        auth=("listener_1", "supersecret"),
        content="",
        headers={"Content-Type": "text/plain"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert "empty-list" in response.headers["location"]


def test_create_podcast_list_with_unicode_title(client: TestClient) -> None:
    register_user(client)

    response = client.post(
        "/api/2/lists/listener_1/create.json?title=Podcasts%20em%20Portugu%C3%AAs",
        auth=("listener_1", "supersecret"),
        json=["https://example.com/feed.xml"],
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert "podcasts-em-portugues" in response.headers["location"]


def test_get_user_podcast_lists_returns_empty_array_for_user_without_lists(
    client: TestClient,
) -> None:
    register_user(client)

    response = client.get("/api/2/lists/listener_1.json")

    assert response.status_code == 200
    assert response.json() == []


def test_update_podcast_list_with_different_format(
    client: TestClient, settings: Settings
) -> None:
    register_user(client)
    seed_list_state(settings)

    updated = client.put(
        "/api/2/lists/listener_1/list/my-python-podcasts.json",
        auth=("listener_1", "supersecret"),
        json=["https://example.com/feed-c.xml"],
    )

    assert updated.status_code == 204

    verify = client.get("/api/2/lists/listener_1/list/my-python-podcasts.json")
    assert verify.status_code == 200
    assert [item["url"] for item in verify.json()["podcasts"]] == [
        "https://example.com/feed-c.xml",
    ]


def test_create_podcast_list_without_auth_returns_401(client: TestClient) -> None:
    register_user(client)

    response = client.post(
        "/api/2/lists/listener_1/create.json?title=Secret%20List",
        json=["https://example.com/feed.xml"],
        follow_redirects=False,
    )

    assert response.status_code == 401
