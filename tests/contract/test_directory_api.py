from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

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


def seed_directory_state(settings: Settings) -> dict[str, str]:
    db_path = sqlite_path(settings)
    now = datetime.now(UTC)
    feed_linux = "https://example.com/linux.xml"
    feed_tech = "https://example.com/tech.xml"
    feed_orphan = "https://example.com/orphan.xml"
    episode_url = "https://cdn.example.com/linux-001.mp3"

    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()

        for nickname, device_id in [
            ("listener_1", "phone-01"),
            ("listener_2", "phone-02"),
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
            INSERT INTO podcast_feeds
                (
                    feed_url, title, author, description, website, logo_url, mygpo_link,
                    categories, created_at, updated_at
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                feed_tech,
                "Tech Talk",
                "Host B",
                "Technology news",
                "https://example.com/tech",
                None,
                None,
                json.dumps(["technology"]),
                now.isoformat(),
                now.isoformat(),
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
                feed_orphan,
                "Orphan Feed",
                None,
                None,
                None,
                None,
                None,
                json.dumps(["technology"]),
                now.isoformat(),
                now.isoformat(),
            ),
        )

        for device_id, feed_url in [
            ("phone-01", feed_linux),
            ("phone-02", feed_linux),
            ("phone-01", feed_tech),
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
                episode_url,
                "Episode 1",
                "An episode",
                "https://example.com/linux/ep1",
                None,
                now.isoformat(),
                now.isoformat(),
                now.isoformat(),
                feed_linux,
            ),
        )
        connection.commit()

    return {
        "feed_linux": feed_linux,
        "feed_tech": feed_tech,
        "feed_orphan": feed_orphan,
        "episode_url": episode_url,
    }


def test_search_contract_returns_matches_and_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BASE_URL", "https://directory.example/")
    clear_settings_cache()
    settings = get_settings()

    with TestClient(create_app()) as client:
        register_user(client, "listener_1")
        register_user(client, "listener_2")
        seeded = seed_directory_state(settings)

        matches = client.get("/search.json?q=linux")
        empty = client.get("/search.json?q=does-not-exist")

    assert matches.status_code == 200
    urls = [item["url"] for item in matches.json()]
    assert seeded["feed_linux"] in urls
    assert seeded["feed_orphan"] not in urls

    assert empty.status_code == 200
    assert empty.json() == []


def test_search_contract_opml_and_txt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BASE_URL", "https://directory.example/")
    clear_settings_cache()
    settings = get_settings()

    with TestClient(create_app()) as client:
        register_user(client, "listener_1")
        register_user(client, "listener_2")
        seeded = seed_directory_state(settings)

        opml = client.get("/search.opml?q=linux")
        txt = client.get("/search.txt?q=linux")

    assert opml.status_code == 200
    assert "<opml" in opml.text.lower()
    assert seeded["feed_linux"] in opml.text

    assert txt.status_code == 200
    assert seeded["feed_linux"] in txt.text.splitlines()


def test_toplist_contract_orders_limits_and_validates_number(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BASE_URL", "https://directory.example/")
    clear_settings_cache()
    settings = get_settings()

    with TestClient(create_app()) as client:
        register_user(client, "listener_1")
        register_user(client, "listener_2")
        seeded = seed_directory_state(settings)

        toplist = client.get("/toplist/10.json")
        limited = client.get("/toplist/1.json")
        invalid_low = client.get("/toplist/0.json")
        invalid_high = client.get("/toplist/101.json")

    assert toplist.status_code == 200
    payload = toplist.json()
    assert payload[0]["url"] == seeded["feed_linux"]
    assert payload[0]["subscribers"] == 2
    assert payload[0]["author"] == "Host A"
    assert any(item["url"] == seeded["feed_tech"] for item in payload)

    assert limited.status_code == 200
    assert len(limited.json()) == 1
    assert limited.json()[0]["url"] == seeded["feed_linux"]

    assert invalid_low.status_code == 400
    assert invalid_high.status_code == 400


def test_tags_contract_lists_tags_and_podcasts_by_tag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BASE_URL", "https://directory.example/")
    clear_settings_cache()
    settings = get_settings()

    with TestClient(create_app()) as client:
        register_user(client, "listener_1")
        register_user(client, "listener_2")
        seeded = seed_directory_state(settings)

        tags = client.get("/api/2/tags/10.json")
        technology = client.get("/api/2/tag/technology/10.json")
        missing = client.get("/api/2/tag/missing/10.json")
        invalid = client.get("/api/2/tags/0.json")

    assert tags.status_code == 200
    payload = tags.json()
    by_tag = {item["tag"]: item for item in payload}
    assert by_tag["technology"]["usage"] == 2

    assert technology.status_code == 200
    urls = [item["url"] for item in technology.json()]
    assert seeded["feed_linux"] in urls
    assert seeded["feed_tech"] in urls
    assert seeded["feed_orphan"] not in urls

    assert missing.status_code == 200
    assert missing.json() == []

    assert invalid.status_code == 400


def test_podcast_and_episode_data_contracts_return_200_or_404(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BASE_URL", "https://directory.example/")
    clear_settings_cache()
    settings = get_settings()

    with TestClient(create_app()) as client:
        register_user(client, "listener_1")
        register_user(client, "listener_2")
        seeded = seed_directory_state(settings)

        podcast = client.get(f"/api/2/data/podcast.json?url={seeded['feed_linux']}")
        unknown_podcast = client.get(
            "/api/2/data/podcast.json?url=https://unknown.example/feed.xml"
        )
        episode = client.get(
            f"/api/2/data/episode.json?podcast={seeded['feed_linux']}&url={seeded['episode_url']}"
        )
        unknown_episode = client.get(
            f"/api/2/data/episode.json?podcast={seeded['feed_linux']}&url=https://unknown.example/missing.mp3"
        )

    assert podcast.status_code == 200
    payload = podcast.json()
    assert set(payload) >= {
        "url",
        "title",
        "author",
        "description",
        "subscribers",
        "logo_url",
        "website",
        "mygpo_link",
    }
    assert payload["subscribers"] == 2
    assert payload["mygpo_link"].startswith("https://directory.example/")

    assert unknown_podcast.status_code == 404

    assert episode.status_code == 200
    episode_payload = episode.json()
    assert set(episode_payload) >= {
        "title",
        "url",
        "podcast_title",
        "podcast_url",
        "description",
        "website",
        "released",
        "mygpo_link",
    }
    assert episode_payload["podcast_url"] == seeded["feed_linux"]
    assert episode_payload["mygpo_link"].startswith("https://directory.example/")

    assert unknown_episode.status_code == 404
