from __future__ import annotations

import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from tests.contract.test_sync_devices_api import create_device
from tests.integration.test_profile_page import register_and_login

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

    from app.core.config import Settings


def sqlite_path(settings: Settings) -> Path:
    return Path(settings.test_database_url.removeprefix("sqlite+aiosqlite:///"))


def seed_feed(settings: Settings, *, title: str) -> int:
    db_path = sqlite_path(settings)
    now = datetime.now(UTC)
    unique = uuid.uuid4().hex
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
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
                f"https://example.com/feed-{unique}.xml",
                title,
                None,
                None,
                None,
                None,
                None,
                None,
                now.isoformat(),
                now.isoformat(),
            ),
        )
        assert cursor.lastrowid is not None
        feed_id = int(cursor.lastrowid)
        connection.commit()
        return feed_id


def seed_episode(
    settings: Settings,
    *,
    feed_id: int,
    episode_url: str,
    title: str,
) -> int:
    db_path = sqlite_path(settings)
    now = datetime.now(UTC)
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO episodes
                (
                    feed_id, episode_url, title, description, website, media_url,
                    mygpo_link, logo_url, released_at, created_at, updated_at
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                feed_id,
                episode_url,
                title,
                None,
                None,
                None,
                None,
                None,
                now.isoformat(),
                now.isoformat(),
                now.isoformat(),
            ),
        )
        assert cursor.lastrowid is not None
        episode_id = int(cursor.lastrowid)
        connection.commit()
        return episode_id


def seed_subscription(settings: Settings, *, feed_id: int) -> None:
    db_path = sqlite_path(settings)
    now = datetime.now(UTC)
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO device_subscriptions
                (device_pk, feed_id, subscribed_at, unsubscribed_at, updated_at)
            SELECT devices.id, ?, ?, NULL, ?
            FROM devices
            WHERE devices.device_id = ?
            """,
            (
                feed_id,
                now.isoformat(),
                now.isoformat(),
                "web",
            ),
        )
        connection.commit()


def seed_play_event(
    settings: Settings,
    *,
    episode_id: int,
    feed_id: int,
    position: int,
    total: int,
    occurred_at: datetime,
) -> None:
    db_path = sqlite_path(settings)
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO episode_action_events
                (
                    user_id, episode_id, podcast_url, episode_url, device_id, action,
                    occurred_at, started, position, total, created_at
                )
            SELECT
                users.id,
                ?,
                podcast_feeds.feed_url,
                episodes.episode_url,
                ?,
                ?,
                ?,
                NULL,
                ?,
                ?,
                ?
            FROM users, podcast_feeds, episodes
            WHERE users.nickname = ?
              AND podcast_feeds.id = ?
              AND episodes.id = ?
            """,
            (
                episode_id,
                "web",
                "play",
                occurred_at.isoformat(),
                position,
                total,
                occurred_at.isoformat(),
                "listener_1",
                feed_id,
                episode_id,
            ),
        )
        connection.commit()


def test_user_stats_page_redirects_when_logged_out(
    client: TestClient,
) -> None:
    response = client.get("/user/listener_1/stats", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_user_stats_page_is_private_to_current_user(
    client: TestClient,
) -> None:
    register_and_login(client)

    response = client.get("/user/someone_else/stats")

    assert response.status_code == 404


def test_user_stats_page_renders_totals_and_rankings(
    client: TestClient,
    settings: Settings,
) -> None:
    register_and_login(client)
    create_device(client, username="listener_1", device_id="web")

    feed_a = seed_feed(settings, title="Podcast Alpha")
    feed_b = seed_feed(settings, title="Podcast Beta")

    seed_subscription(settings, feed_id=feed_a)
    seed_subscription(settings, feed_id=feed_b)

    ep_a1 = seed_episode(
        settings, feed_id=feed_a, episode_url="https://example.com/a1", title="A1"
    )
    ep_a2 = seed_episode(
        settings, feed_id=feed_a, episode_url="https://example.com/a2", title="A2"
    )
    ep_b1 = seed_episode(
        settings, feed_id=feed_b, episode_url="https://example.com/b1", title="B1"
    )

    now = datetime.now(UTC)
    seed_play_event(
        settings,
        episode_id=ep_a1,
        feed_id=feed_a,
        position=120,
        total=120,
        occurred_at=now,
    )
    seed_play_event(
        settings,
        episode_id=ep_a2,
        feed_id=feed_a,
        position=60,
        total=120,
        occurred_at=now,
    )
    seed_play_event(
        settings,
        episode_id=ep_b1,
        feed_id=feed_b,
        position=30,
        total=120,
        occurred_at=now,
    )

    response = client.get("/user/listener_1/stats")

    assert response.status_code == 200
    assert '<html lang="pt-BR">' in response.text
    assert "Podcast Alpha" in response.text
    assert "Podcast Beta" in response.text


def test_user_stats_page_renders_empty_state_with_no_play_data(
    client: TestClient,
    settings: Settings,
) -> None:
    register_and_login(client)
    create_device(client, username="listener_1", device_id="web")

    feed_id = seed_feed(settings, title="Silent Podcast")
    seed_subscription(settings, feed_id=feed_id)
    seed_episode(
        settings,
        feed_id=feed_id,
        episode_url="https://example.com/silent-ep1",
        title="Silent Episode",
    )

    response = client.get("/user/listener_1/stats")

    assert response.status_code == 200
    assert "Minhas métricas" in response.text
    assert "0" in response.text
    assert "Ainda não há dados suficientes." in response.text
