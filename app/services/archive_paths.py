from __future__ import annotations

import hashlib
import re
import unicodedata
from pathlib import Path

_NON_SLUG_CHARS = re.compile(r"[^a-z0-9]+")


def slugify_segment(value: str, *, fallback: str = "untitled") -> str:
    cleaned = (value or "").strip()
    if not cleaned:
        return fallback
    cleaned = unicodedata.normalize("NFKD", cleaned).encode("ascii", "ignore").decode()
    cleaned = cleaned.lower()
    cleaned = _NON_SLUG_CHARS.sub("-", cleaned)
    cleaned = cleaned.strip("-")
    return cleaned or fallback


def stable_short_hash(value: str, *, length: int = 8) -> str:
    digest = hashlib.sha256((value or "").encode("utf-8")).hexdigest()
    return digest[:length]


def build_episode_archive_relpath(
    *,
    podcast_title: str,
    episode_title: str,
    episode_url: str,
    ext: str = "mp3",
) -> str:
    podcast_slug = slugify_segment(podcast_title, fallback="podcast")
    title_slug = slugify_segment(episode_title, fallback="episode")
    suffix = stable_short_hash(episode_url or episode_title)
    filename = f"{title_slug}-{suffix}.{ext}"
    return str(Path(podcast_slug) / filename)


def resolve_archive_path(archive_dir: Path, relative_path: str) -> Path:
    rel = Path(relative_path)
    if rel.is_absolute():
        raise ValueError("archive_path must be relative")
    if any(part in {"..", "."} for part in rel.parts):
        raise ValueError("archive_path must not contain dot segments")
    root = archive_dir.resolve()
    full = (archive_dir / rel).resolve()
    if full == root:
        raise ValueError("archive_path must point to a file inside archive_dir")
    if root not in full.parents:
        raise ValueError("resolved archive path escapes archive_dir")
    return full
