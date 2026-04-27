from __future__ import annotations

import pytest

from app.core.media_url import normalize_media_url


@pytest.mark.parametrize(
    "raw, expected",
    [
        # pscrb.fm
        (
            "https://pscrb.fm/rss/p/traffic.omny.fm/d/clips/abc/audio.mp3?foo=bar",
            "https://traffic.omny.fm/d/clips/abc/audio.mp3?foo=bar",
        ),
        # podtrac redirect.mp3
        (
            "https://dts.podtrac.com/redirect.mp3/media.example.com/ep1.mp3",
            "https://media.example.com/ep1.mp3",
        ),
        # podtrac www variant
        (
            "https://www.podtrac.com/pts/redirect.mp3/media.example.com/ep2.mp3",
            "https://media.example.com/ep2.mp3",
        ),
        # op3.dev
        (
            "https://op3.dev/e/media.example.com/ep3.mp3",
            "https://media.example.com/ep3.mp3",
        ),
        # pdst.fm (podscribe)
        (
            "https://pdst.fm/e/media.example.com/ep4.mp3",
            "https://media.example.com/ep4.mp3",
        ),
        # chartable (has tracker ID segment)
        (
            "https://chtbl.com/track/ABCDE/media.example.com/ep5.mp3",
            "https://media.example.com/ep5.mp3",
        ),
        # direct URL — unchanged
        (
            "https://traffic.omny.fm/d/clips/abc/audio.mp3",
            "https://traffic.omny.fm/d/clips/abc/audio.mp3",
        ),
        # http scheme — unchanged
        (
            "http://media.example.com/ep.mp3",
            "http://media.example.com/ep.mp3",
        ),
    ],
)
def test_normalize_media_url(raw: str, expected: str) -> None:
    assert normalize_media_url(raw) == expected
