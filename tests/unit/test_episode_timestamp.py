from __future__ import annotations

from datetime import UTC, datetime, timezone

from app.schemas.episode import EpisodeActionInput


def _build(timestamp: str | None = None) -> dict[str, object]:
    payload: dict[str, object] = {
        "podcast": "https://example.com/feed.xml",
        "episode": "https://example.com/ep.mp3",
        "action": "download",
    }
    if timestamp is not None:
        payload["timestamp"] = timestamp
    return payload


def test_naive_iso_timestamp_treated_as_utc() -> None:
    action = EpisodeActionInput.model_validate(_build("2026-04-17T19:00:00"))
    assert action.timestamp is not None
    assert action.timestamp.tzinfo is not None
    assert action.timestamp == datetime(2026, 4, 17, 19, 0, tzinfo=UTC)


def test_timestamp_with_space_separator() -> None:
    action = EpisodeActionInput.model_validate(_build("2026-04-17 19:00:00"))
    assert action.timestamp is not None
    assert action.timestamp.tzinfo is not None


def test_timestamp_with_z_suffix() -> None:
    action = EpisodeActionInput.model_validate(_build("2026-04-17T19:00:00Z"))
    assert action.timestamp is not None
    assert action.timestamp == datetime(2026, 4, 17, 19, 0, tzinfo=UTC)


def test_timestamp_with_offset() -> None:
    action = EpisodeActionInput.model_validate(_build("2026-04-17T19:00:00+02:00"))
    assert action.timestamp is not None
    tz = timezone(offset=__import__("datetime").timedelta(hours=2))
    assert action.timestamp == datetime(2026, 4, 17, 19, 0, tzinfo=tz)


def test_null_timestamp_accepted() -> None:
    action = EpisodeActionInput.model_validate(_build())
    assert action.timestamp is None


def test_negative_offset_preserved() -> None:
    action = EpisodeActionInput.model_validate(_build("2026-04-17T19:00:00-03:00"))
    assert action.timestamp is not None
    assert action.timestamp.utcoffset().total_seconds() == -3 * 3600  # type: ignore[union-attr]
