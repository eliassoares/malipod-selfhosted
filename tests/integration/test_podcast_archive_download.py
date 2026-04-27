from __future__ import annotations

import http.server
import socket
import sqlite3
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi.testclient import TestClient

from app.core.config import clear_settings_cache, get_settings
from app.main import create_app
from tests.integration.test_profile_page import register_and_login

if TYPE_CHECKING:
    from pytest import MonkeyPatch

    from app.core.config import Settings


def sqlite_path(settings: Settings) -> Path:
    return Path(settings.test_database_url.removeprefix("sqlite+aiosqlite:///"))


class _AudioHandler(http.server.BaseHTTPRequestHandler):
    audio_bytes = b"FAKE-MP3-DATA"

    def do_GET(self) -> None:
        if self.path != "/audio.mp3":
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "audio/mpeg")
        self.send_header("Content-Length", str(len(self.audio_bytes)))
        self.end_headers()
        self.wfile.write(self.audio_bytes)

    def log_message(self, *_: object, **__: object) -> None:
        return


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def seed_podcast(settings: Settings, *, media_url: str) -> tuple[int, int]:
    db_path = sqlite_path(settings)
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO podcast_feeds
                (
                    feed_url, title, author, description, website, logo_url, mygpo_link,
                    categories, created_at, updated_at, archive
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), 0)
            """,
            (
                "https://example.com/feed.xml",
                "Example Podcast",
                None,
                None,
                None,
                None,
                None,
                None,
            ),
        )
        assert cursor.lastrowid is not None
        feed_id = int(cursor.lastrowid)
        cursor.execute(
            """
            INSERT INTO episodes
                (
                    feed_id, episode_url, title, description, website, media_url,
                    mygpo_link,
                    logo_url, released_at, created_at, updated_at,
                    archive_status, archive_path, archive_error
                )
            VALUES
                (
                    ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'),
                    datetime('now'), 'none', NULL, NULL
                )
            """,
            (
                feed_id,
                "https://example.com/ep-1",
                "Episode One",
                None,
                None,
                media_url,
                None,
                None,
            ),
        )
        assert cursor.lastrowid is not None
        episode_id = int(cursor.lastrowid)
        connection.commit()
    return feed_id, episode_id


def test_archive_enable_downloads_episode_to_disk(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    archive_dir = tmp_path / "archive"
    monkeypatch.setenv("ARCHIVE_DIR", str(archive_dir))
    monkeypatch.setenv("ARCHIVE_WORKERS", "1")
    monkeypatch.setenv("ARCHIVE_SYNC_INTERVAL_MINUTES", "9999")
    clear_settings_cache()

    port = _free_port()
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), _AudioHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        settings = get_settings()
        feed_id, episode_id = seed_podcast(
            settings, media_url=f"http://127.0.0.1:{port}/audio.mp3"
        )

        with TestClient(create_app()) as client:
            register_and_login(client)

            response = client.post(
                f"/podcast/{feed_id}/archive", follow_redirects=False
            )
            assert response.status_code == 303

            db_path = sqlite_path(settings)
            deadline = time.time() + 5.0
            archive_path: str | None = None
            status: str | None = None
            while time.time() < deadline:
                with sqlite3.connect(db_path) as connection:
                    cursor = connection.cursor()
                    cursor.execute(
                        (
                            "SELECT archive_status, archive_path "
                            "FROM episodes WHERE id = ?"
                        ),
                        (episode_id,),
                    )
                    row = cursor.fetchone()
                    assert row is not None
                    status, archive_path = row
                if status == "done" and archive_path:
                    break
                time.sleep(0.1)

            assert status == "done"
            assert archive_path is not None
            assert (archive_dir / archive_path).exists()
    finally:
        server.shutdown()
