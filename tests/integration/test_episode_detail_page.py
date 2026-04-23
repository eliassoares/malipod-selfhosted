from __future__ import annotations

import sqlite3
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

from tests.integration.test_profile_page import register_and_login

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

    from app.core.config import Settings


def sqlite_path(settings: Settings) -> Path:
    return Path(settings.test_database_url.removeprefix("sqlite+aiosqlite:///"))


def seed_episode(
    settings: Settings, *, media_url: str | None = None
) -> tuple[int, str, str]:
    db_path = sqlite_path(settings)
    now = datetime.now(UTC)
    unique = uuid.uuid4().hex
    feed_url = f"https://example.com/feed-{unique}.xml"
    episode_url = f"https://example.com/ep-{unique}"
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
                feed_url,
                "Example Podcast",
                "Example Author",
                "A description for the podcast.",
                "https://example.com",
                None,
                None,
                None,
                now.isoformat(),
                now.isoformat(),
            ),
        )
        feed_rowid = cursor.lastrowid
        assert feed_rowid is not None
        feed_id = int(feed_rowid)
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
                "Episode One",
                "Ep 1 description",
                None,
                media_url,
                None,
                None,
                now.isoformat(),
                now.isoformat(),
                now.isoformat(),
            ),
        )
        episode_rowid = cursor.lastrowid
        assert episode_rowid is not None
        connection.commit()
        return int(episode_rowid), feed_url, episode_url


def seed_progress(
    settings: Settings, *, episode_id: int, position: int, total: int
) -> None:
    db_path = sqlite_path(settings)
    now = datetime.now(UTC)
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO episode_actions
                (
                    user_id, device_pk, episode_id, status, action, occurred_at,
                    updated_at
                )
            SELECT users.id, NULL, ?, ?, ?, ?, ?
            FROM users
            WHERE users.nickname = ?
            """,
            (
                episode_id,
                "play",
                f'{{"position": {position}, "total": {total}}}',
                now.isoformat(),
                now.isoformat(),
                "listener_1",
            ),
        )
        connection.commit()


def seed_history(
    settings: Settings, *, episode_id: int, feed_url: str, episode_url: str
) -> None:
    db_path = sqlite_path(settings)
    now = datetime.now(UTC)
    earlier = now - timedelta(hours=2)
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO episode_action_events
                (
                    user_id, episode_id, podcast_url, episode_url, device_id, action,
                    occurred_at, started, position, total, created_at
                )
            SELECT users.id, ?, ?, ?, NULL, ?, ?, NULL, ?, ?, ?
            FROM users
            WHERE users.nickname = ?
            """,
            (
                episode_id,
                feed_url,
                episode_url,
                "play",
                earlier.isoformat(),
                30,
                120,
                now.isoformat(),
                "listener_1",
            ),
        )
        connection.commit()


def seed_play_event(
    settings: Settings,
    *,
    episode_id: int,
    feed_url: str,
    episode_url: str,
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
            SELECT users.id, ?, ?, ?, NULL, ?, ?, NULL, ?, ?, ?
            FROM users
            WHERE users.nickname = ?
            """,
            (
                episode_id,
                feed_url,
                episode_url,
                "play",
                occurred_at.isoformat(),
                30,
                120,
                occurred_at.isoformat(),
                "listener_1",
            ),
        )
        connection.commit()


def seed_favorite(
    settings: Settings, *, episode_id: int, favorited_at: datetime
) -> None:
    db_path = sqlite_path(settings)
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO favorite_episodes
                (user_id, episode_id, favorited_at, created_at, updated_at)
            SELECT users.id, ?, ?, ?, ?
            FROM users
            WHERE users.nickname = ?
            """,
            (
                episode_id,
                favorited_at.isoformat(),
                favorited_at.isoformat(),
                favorited_at.isoformat(),
                "listener_1",
            ),
        )
        connection.commit()


def test_episode_detail_page_redirects_when_logged_out(
    client: TestClient,
    settings: Settings,
) -> None:
    episode_id, _, _ = seed_episode(settings)

    response = client.get(f"/episode/{episode_id}", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_episode_detail_page_returns_404_for_missing_episode(
    client: TestClient,
    settings: Settings,
) -> None:
    register_and_login(client)

    response = client.get("/episode/999999")

    assert response.status_code == 404
    assert "Episódio não encontrado" in response.text
    assert '<html lang="pt-BR">' in response.text


def test_episode_detail_page_renders_metadata_and_placeholder(
    client: TestClient,
    settings: Settings,
) -> None:
    register_and_login(client)
    episode_id, _, _ = seed_episode(settings)

    response = client.get(f"/episode/{episode_id}")

    assert response.status_code == 200
    assert "Episode One" in response.text
    assert "Example Podcast" in response.text
    assert "/static/placeholders/" in response.text


def test_episode_detail_page_renders_progress_when_present(
    client: TestClient,
    settings: Settings,
) -> None:
    register_and_login(client)
    episode_id, _, _ = seed_episode(settings)
    seed_progress(settings, episode_id=episode_id, position=30, total=120)

    response = client.get(f"/episode/{episode_id}")

    assert response.status_code == 200
    assert "Progresso" in response.text
    assert "25%" in response.text
    assert "30s de 2min" in response.text


def test_episode_detail_page_download_visibility_and_redirect(
    client: TestClient,
    settings: Settings,
) -> None:
    register_and_login(client)

    without_media, _, _ = seed_episode(settings, media_url=None)
    no_link = client.get(f"/episode/{without_media}")
    assert no_link.status_code == 200
    assert f"/episode/{without_media}/download" not in no_link.text
    assert "cursor-not-allowed" in no_link.text

    with_media, _, _ = seed_episode(
        settings, media_url="https://cdn.example.com/ep-1.mp3"
    )
    has_link = client.get(f"/episode/{with_media}")
    assert has_link.status_code == 200
    assert f"/episode/{with_media}/download" in has_link.text
    assert "Baixar" in has_link.text

    async def _fake_stream(**_: object) -> object:
        yield b"audio"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-type": "audio/mpeg", "content-length": "5"}
    mock_resp.aiter_bytes = _fake_stream
    mock_resp.aclose = AsyncMock()

    mock_client = AsyncMock()
    mock_client.send = AsyncMock(return_value=mock_resp)
    mock_client.aclose = AsyncMock()

    _target = "app.api.routes.episode_site.httpx.AsyncClient"
    with patch(_target, return_value=mock_client):
        download = client.get(f"/episode/{with_media}/download")
    assert download.status_code == 200
    assert "attachment" in download.headers.get("content-disposition", "")
    assert "Episode_One" in download.headers.get("content-disposition", "")


def test_episode_detail_page_renders_share_link(
    client: TestClient,
    settings: Settings,
) -> None:
    register_and_login(client)
    episode_id, _, _ = seed_episode(settings)

    response = client.get(f"/episode/{episode_id}")

    assert response.status_code == 200
    assert "Compartilhar" in response.text
    assert f"{settings.base_url.rstrip('/')}/episode/{episode_id}" in response.text


def test_episode_detail_page_can_toggle_favorite(
    client: TestClient,
    settings: Settings,
) -> None:
    register_and_login(client)
    episode_id, _, _ = seed_episode(settings)

    before = client.get(f"/episode/{episode_id}")
    assert before.status_code == 200
    assert "Favoritar" in before.text

    toggled = client.post(
        f"/episode/{episode_id}/favorite",
        follow_redirects=False,
    )
    assert toggled.status_code == 303

    after = client.get(f"/episode/{episode_id}")
    assert after.status_code == 200
    assert "Remover favorito" in after.text


def test_episode_detail_page_renders_history_events_and_empty_state(
    client: TestClient,
    settings: Settings,
) -> None:
    register_and_login(client)
    episode_id, feed_url, episode_url = seed_episode(settings)

    empty = client.get(f"/episode/{episode_id}")
    assert empty.status_code == 200
    assert "Histórico de ouvidas" in empty.text
    assert "Nenhum histórico ainda." in empty.text

    seed_history(
        settings, episode_id=episode_id, feed_url=feed_url, episode_url=episode_url
    )
    filled = client.get(f"/episode/{episode_id}")
    assert filled.status_code == 200
    assert "Nenhum histórico ainda." not in filled.text
    assert "play" in filled.text


def test_episode_detail_page_renders_play_count_and_first_last_play(
    client: TestClient,
    settings: Settings,
) -> None:
    register_and_login(client)
    episode_id, feed_url, episode_url = seed_episode(settings)

    first = datetime(2026, 4, 20, 12, 0, tzinfo=UTC)
    last = datetime(2026, 4, 22, 13, 0, tzinfo=UTC)
    seed_play_event(
        settings,
        episode_id=episode_id,
        feed_url=feed_url,
        episode_url=episode_url,
        occurred_at=first,
    )
    seed_play_event(
        settings,
        episode_id=episode_id,
        feed_url=feed_url,
        episode_url=episode_url,
        occurred_at=last,
    )

    response = client.get(f"/episode/{episode_id}")

    assert response.status_code == 200
    assert "Vezes reproduzido" in response.text
    assert "2" in response.text
    assert "Primeiro play" in response.text
    assert "Último play" in response.text


def test_episode_detail_page_renders_favorited_timestamp_when_favorited(
    client: TestClient,
    settings: Settings,
) -> None:
    register_and_login(client)
    episode_id, _, _ = seed_episode(settings)

    favorited_at = datetime(2026, 4, 21, 9, 0, tzinfo=UTC)
    seed_favorite(settings, episode_id=episode_id, favorited_at=favorited_at)

    response = client.get(f"/episode/{episode_id}")

    assert response.status_code == 200
    assert "Favoritado em" in response.text
    assert "2026-04-21" in response.text


def test_download_redirects_to_login_when_not_authenticated(
    client: TestClient,
    settings: Settings,
) -> None:
    episode_id, _, _ = seed_episode(
        settings, media_url="https://cdn.example.com/ep.mp3"
    )

    response = client.get(f"/episode/{episode_id}/download", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_favorite_redirects_to_login_when_not_authenticated(
    client: TestClient,
    settings: Settings,
) -> None:
    episode_id, _, _ = seed_episode(settings)

    response = client.post(f"/episode/{episode_id}/favorite", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_download_redirects_to_episode_when_no_media_url(
    client: TestClient,
    settings: Settings,
) -> None:
    register_and_login(client)
    episode_id, _, _ = seed_episode(settings, media_url=None)

    response = client.get(f"/episode/{episode_id}/download", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == f"/episode/{episode_id}"


def test_download_rejects_non_http_scheme(
    client: TestClient,
    settings: Settings,
) -> None:
    register_and_login(client)
    episode_id, _, _ = seed_episode(settings, media_url="javascript:alert(1)")

    response = client.get(f"/episode/{episode_id}/download", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == f"/episode/{episode_id}"
