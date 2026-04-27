from __future__ import annotations

from pathlib import Path

import pytest

from app.services.archive_paths import (
    build_episode_archive_relpath,
    resolve_archive_path,
    slugify_segment,
    stable_short_hash,
)


def test_slugify_segment_normalizes_text() -> None:
    assert slugify_segment("  Hello, World! ") == "hello-world"
    assert slugify_segment("Áudio & Café") == "udio-caf"


def test_slugify_segment_falls_back_when_empty() -> None:
    assert slugify_segment("") == "untitled"
    assert slugify_segment("   ", fallback="x") == "x"


def test_stable_short_hash_is_deterministic() -> None:
    assert stable_short_hash("abc") == stable_short_hash("abc")
    assert stable_short_hash("abc") != stable_short_hash("abcd")


def test_build_episode_archive_relpath_contains_slug_and_hash() -> None:
    relpath = build_episode_archive_relpath(
        podcast_title="My Podcast",
        episode_title="Episode One",
        episode_url="https://example.com/audio.mp3",
    )
    assert relpath.startswith("my-podcast/")
    assert relpath.endswith(".mp3")
    assert "-" in Path(relpath).name


def test_resolve_archive_path_rejects_absolute_and_dot_segments(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        resolve_archive_path(tmp_path, "/etc/passwd")
    with pytest.raises(ValueError):
        resolve_archive_path(tmp_path, "../escape.mp3")


def test_resolve_archive_path_stays_within_root(tmp_path: Path) -> None:
    full = resolve_archive_path(tmp_path, "podcast/episode.mp3")
    assert str(full).startswith(str(tmp_path.resolve()))
