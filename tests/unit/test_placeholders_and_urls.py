from __future__ import annotations

from app.core.placeholders import (
    PLACEHOLDER_URLS,
    choose_placeholder_url_random,
    choose_placeholder_url_stable,
)
from app.core.security import sanitize_subscription_url


def test_choose_placeholder_random_returns_known_url() -> None:
    assert choose_placeholder_url_random() in PLACEHOLDER_URLS


def test_choose_placeholder_stable_is_deterministic() -> None:
    first = choose_placeholder_url_stable("https://example.com/feed.xml")
    second = choose_placeholder_url_stable("https://example.com/feed.xml")
    assert first == second
    assert first in PLACEHOLDER_URLS


def test_sanitize_subscription_url_requires_http_or_https() -> None:
    assert sanitize_subscription_url("ftp://example.com") == ""
    assert (
        sanitize_subscription_url("https://example.com/feed.xml")
        == "https://example.com/feed.xml"
    )
