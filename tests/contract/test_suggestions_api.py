from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import quote

from fastapi.testclient import TestClient

from app.core.config import clear_settings_cache, get_settings
from app.main import create_app

if TYPE_CHECKING:
    import pytest

    from app.core.config import Settings


def register_user(client: TestClient, nickname: str) -> None:
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


def seed_suggestions_state(settings: Settings) -> dict[str, str]:
    db_path = sqlite_path(settings)
    now = datetime.now(UTC)
    feed_linux = "https://example.com/linux.xml"
    feed_tech = "https://example.com/tech.xml"
    feed_orphan = "https://example.com/orphan.xml"

    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()

        for nickname, device_id in [
            ("listener_1", "phone-01"),
            ("listener_2", "phone-02"),
            ("listener_3", "phone-03"),
        ]:
            cursor.execute(
                """
                INSERT INTO devices (
                    user_id, device_id, caption, device_type, created_at, updated_at
                )
                SELECT id, ?, ?, ?, ?, ? FROM users WHERE nickname = ?
                """,
                (
                    device_id,
                    device_id,
                    "mobile",
                    now.isoformat(),
                    now.isoformat(),
                    nickname,
                ),
            )

        for feed_url, title, author in [
            (feed_linux, "Linux Weekly", "Host A"),
            (feed_tech, "Tech Talk", "Host B"),
            (feed_orphan, "Orphan Feed", None),
        ]:
            cursor.execute(
                """
                INSERT INTO podcast_feeds
                    (
                        feed_url, title, author, description, website, logo_url,
                        mygpo_link, categories, created_at, updated_at
                    )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    feed_url,
                    title,
                    author,
                    f"Description for {title}" if title else None,
                    f"https://example.com/{title}" if title else None,
                    None,
                    None,
                    json.dumps(["technology"]),
                    now.isoformat(),
                    now.isoformat(),
                ),
            )

        for device_id, feed_url in [
            ("phone-01", feed_linux),
            ("phone-03", feed_linux),
            ("phone-02", feed_tech),
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

    return {
        "feed_linux": feed_linux,
        "feed_tech": feed_tech,
        "feed_orphan": feed_orphan,
    }


def seed_single_user_state(settings: Settings, nickname: str) -> str:
    db_path = sqlite_path(settings)
    now = datetime.now(UTC)
    feed_linux = "https://example.com/linux.xml"

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
                "phone-01",
                "mobile",
                now.isoformat(),
                now.isoformat(),
                nickname,
            ),
        )
        cursor.execute(
            """
            INSERT INTO podcast_feeds
                (
                    feed_url, title, author, description, website, logo_url, mygpo_link,
                    categories, created_at, updated_at
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                feed_linux,
                "Linux Weekly",
                "Host A",
                "A linux podcast",
                "https://example.com/linux",
                None,
                None,
                json.dumps(["technology", "linux"]),
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
            (now.isoformat(), now.isoformat(), "phone-01", feed_linux),
        )
        connection.commit()
    return feed_linux


def test_suggestions_contract_requires_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BASE_URL", "https://suggest.example/")
    clear_settings_cache()
    settings = get_settings()

    with TestClient(create_app()) as client:
        register_user(client, "listener_1")
        register_user(client, "listener_2")
        register_user(client, "listener_3")
        seed_suggestions_state(settings)

        response = client.get("/suggestions/10.json")

    assert response.status_code == 401
    assert response.headers.get("WWW-Authenticate") == "Basic"


def test_suggestions_contract_returns_ranked_excludes_and_limits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BASE_URL", "https://suggest.example/")
    clear_settings_cache()
    settings = get_settings()

    with TestClient(create_app()) as client:
        register_user(client, "listener_1")
        register_user(client, "listener_2")
        register_user(client, "listener_3")
        seeded = seed_suggestions_state(settings)

        response = client.get(
            "/suggestions/5.json",
            auth=("listener_2", "supersecret"),
        )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) <= 5
    urls = [item["url"] for item in payload]
    assert seeded["feed_linux"] in urls
    assert seeded["feed_tech"] not in urls
    assert seeded["feed_orphan"] not in urls

    linux_item = next(item for item in payload if item["url"] == seeded["feed_linux"])
    assert linux_item["subscribers"] == 2
    assert linux_item["mygpo_link"] == (
        "https://suggest.example/"
        f"api/2/data/podcast.json?url={quote(seeded['feed_linux'], safe='')}"
    )


def test_suggestions_contract_empty_for_user_without_subscriptions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BASE_URL", "https://suggest.example/")
    clear_settings_cache()
    settings = get_settings()

    with TestClient(create_app()) as client:
        register_user(client, "listener_1")
        register_user(client, "listener_2")
        register_user(client, "listener_3")
        register_user(client, "nosub_usr")
        seed_suggestions_state(settings)

        response = client.get(
            "/suggestions/10.json",
            auth=("nosub_usr", "supersecret"),
        )

    assert response.status_code == 200
    assert response.json() == []


def test_suggestions_contract_empty_for_single_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BASE_URL", "https://suggest.example/")
    clear_settings_cache()
    settings = get_settings()

    with TestClient(create_app()) as client:
        register_user(client, "listener_1")
        seed_single_user_state(settings, "listener_1")

        response = client.get(
            "/suggestions/10.json",
            auth=("listener_1", "supersecret"),
        )

    assert response.status_code == 200
    assert response.json() == []


def test_suggestions_contract_validates_number_and_format(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BASE_URL", "https://suggest.example/")
    clear_settings_cache()
    settings = get_settings()

    with TestClient(create_app()) as client:
        register_user(client, "listener_1")
        register_user(client, "listener_2")
        register_user(client, "listener_3")
        seed_suggestions_state(settings)

        invalid_low = client.get(
            "/suggestions/0.json",
            auth=("listener_2", "supersecret"),
        )
        invalid_high = client.get(
            "/suggestions/101.json", auth=("listener_2", "supersecret")
        )
        invalid_format = client.get(
            "/suggestions/10.bad", auth=("listener_2", "supersecret")
        )

    assert invalid_low.status_code == 400
    assert invalid_high.status_code == 400
    assert invalid_format.status_code == 400


def test_suggestions_contract_opml_and_txt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BASE_URL", "https://suggest.example/")
    clear_settings_cache()
    settings = get_settings()

    with TestClient(create_app()) as client:
        register_user(client, "listener_1")
        register_user(client, "listener_2")
        register_user(client, "listener_3")
        seeded = seed_suggestions_state(settings)

        opml = client.get("/suggestions/10.opml", auth=("listener_2", "supersecret"))
        txt = client.get("/suggestions/10.txt", auth=("listener_2", "supersecret"))

    assert opml.status_code == 200
    assert "<opml" in opml.text.lower()
    assert seeded["feed_linux"] in opml.text

    assert txt.status_code == 200
    assert seeded["feed_linux"] in txt.text.splitlines()
