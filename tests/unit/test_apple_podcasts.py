from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from app.services.apple_podcasts import resolve_apple_podcasts_url


def _make_response(status: int, body: bytes) -> MagicMock:
    resp = MagicMock()
    resp.status = status
    resp.read.return_value = body
    return resp


def _itunes_body(feed_url: str) -> bytes:
    return json.dumps(
        {"resultCount": 1, "results": [{"feedUrl": feed_url, "kind": "podcast"}]}
    ).encode()


# ---------------------------------------------------------------------------
# URL pattern detection
# ---------------------------------------------------------------------------


def test_non_apple_url_returns_none() -> None:
    result = resolve_apple_podcasts_url("https://example.com/feed.xml")
    assert result is None


def test_apple_url_without_id_returns_none() -> None:
    result = resolve_apple_podcasts_url("https://podcasts.apple.com/br/podcast/medo")
    assert result is None


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_resolves_feed_url() -> None:
    feed_url = "https://feeds.example.com/podcast.xml"
    resp = _make_response(200, _itunes_body(feed_url))

    with patch("http.client.HTTPSConnection") as mock_cls:
        conn = MagicMock()
        mock_cls.return_value = conn
        conn.getresponse.return_value = resp
        result = resolve_apple_podcasts_url(
            "https://podcasts.apple.com/br/podcast/medo-e-del%C3%ADrio/id1502134265"
        )

    assert result == feed_url


def test_extracts_id_from_url_with_locale() -> None:
    feed_url = "https://feeds.example.com/podcast.xml"
    resp = _make_response(200, _itunes_body(feed_url))

    with patch("http.client.HTTPSConnection") as mock_cls:
        conn = MagicMock()
        mock_cls.return_value = conn
        conn.getresponse.return_value = resp
        result = resolve_apple_podcasts_url(
            "https://podcasts.apple.com/us/podcast/example/id9999999?l=en-GB"
        )

    assert result == feed_url
    # verify correct iTunes ID was used
    call_args = conn.request.call_args
    assert "id=9999999" in call_args[0][1]


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------


def test_itunes_non_200_returns_none() -> None:
    resp = _make_response(404, b"")

    with patch("http.client.HTTPSConnection") as mock_cls:
        conn = MagicMock()
        mock_cls.return_value = conn
        conn.getresponse.return_value = resp
        result = resolve_apple_podcasts_url(
            "https://podcasts.apple.com/br/podcast/x/id1111111"
        )

    assert result is None


def test_itunes_empty_results_returns_none() -> None:
    body = json.dumps({"resultCount": 0, "results": []}).encode()
    resp = _make_response(200, body)

    with patch("http.client.HTTPSConnection") as mock_cls:
        conn = MagicMock()
        mock_cls.return_value = conn
        conn.getresponse.return_value = resp
        result = resolve_apple_podcasts_url(
            "https://podcasts.apple.com/br/podcast/x/id2222222"
        )

    assert result is None


def test_itunes_result_missing_feed_url_returns_none() -> None:
    body = json.dumps({"resultCount": 1, "results": [{"kind": "podcast"}]}).encode()
    resp = _make_response(200, body)

    with patch("http.client.HTTPSConnection") as mock_cls:
        conn = MagicMock()
        mock_cls.return_value = conn
        conn.getresponse.return_value = resp
        result = resolve_apple_podcasts_url(
            "https://podcasts.apple.com/br/podcast/x/id3333333"
        )

    assert result is None


def test_network_error_returns_none() -> None:
    with patch("http.client.HTTPSConnection") as mock_cls:
        conn = MagicMock()
        mock_cls.return_value = conn
        conn.request.side_effect = OSError("network down")
        result = resolve_apple_podcasts_url(
            "https://podcasts.apple.com/br/podcast/x/id4444444"
        )

    assert result is None


def test_invalid_json_returns_none() -> None:
    resp = _make_response(200, b"not json at all")

    with patch("http.client.HTTPSConnection") as mock_cls:
        conn = MagicMock()
        mock_cls.return_value = conn
        conn.getresponse.return_value = resp
        result = resolve_apple_podcasts_url(
            "https://podcasts.apple.com/br/podcast/x/id5555555"
        )

    assert result is None
