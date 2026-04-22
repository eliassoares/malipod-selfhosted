from __future__ import annotations

import textwrap
from unittest.mock import MagicMock, patch

import pytest

from app.services.feed_import import (
    FeedImportError,
    _check_host,
    _fetch_feed_bytes,
    _parse_feed,
)

# ---------------------------------------------------------------------------
# _check_host
# ---------------------------------------------------------------------------


def _addr(ip: str) -> list[tuple[None, None, None, None, tuple[str, int]]]:
    return [(None, None, None, None, (ip, 0))]


def test_check_host_rejects_empty() -> None:
    with pytest.raises(FeedImportError, match="invalid host"):
        _check_host("")


def test_check_host_rejects_localhost() -> None:
    with pytest.raises(FeedImportError, match="invalid host"):
        _check_host("localhost")


def test_check_host_rejects_loopback() -> None:
    with (
        patch("socket.getaddrinfo", return_value=_addr("127.0.0.1")),
        pytest.raises(FeedImportError, match="invalid host"),
    ):
        _check_host("127.0.0.1")


def test_check_host_rejects_private_rfc1918() -> None:
    with (
        patch("socket.getaddrinfo", return_value=_addr("192.168.1.1")),
        pytest.raises(FeedImportError, match="invalid host"),
    ):
        _check_host("192.168.1.1")


def test_check_host_rejects_link_local() -> None:
    with (
        patch("socket.getaddrinfo", return_value=_addr("169.254.0.1")),
        pytest.raises(FeedImportError, match="invalid host"),
    ):
        _check_host("169.254.0.1")


def test_check_host_raises_on_dns_failure() -> None:
    with (
        patch("socket.getaddrinfo", side_effect=OSError("Name not known")),
        pytest.raises(FeedImportError, match="dns resolution failed"),
    ):
        _check_host("nonexistent.invalid")


def test_check_host_accepts_public_ip() -> None:
    with patch("socket.getaddrinfo", return_value=_addr("1.1.1.1")):
        _check_host("example.com")  # should not raise


# ---------------------------------------------------------------------------
# _fetch_feed_bytes — SSRF / scheme guards
# ---------------------------------------------------------------------------


def _mock_response(status: int, body: bytes, location: str | None = None) -> MagicMock:
    resp = MagicMock()
    resp.status = status
    resp.getheader.return_value = location
    resp.read.side_effect = [body, b""]
    return resp


def test_fetch_feed_bytes_rejects_private_host() -> None:
    with (
        patch(
            "app.services.feed_import._check_host",
            side_effect=FeedImportError("invalid host"),
        ),
        pytest.raises(FeedImportError, match="invalid host"),
    ):
        _fetch_feed_bytes("http://192.168.1.1/feed.xml")


def test_fetch_feed_bytes_rejects_non_http_scheme() -> None:
    with pytest.raises(FeedImportError, match="unsupported scheme"):
        _fetch_feed_bytes("ftp://example.com/feed.xml")


def test_fetch_feed_bytes_raises_on_4xx() -> None:
    with (
        patch("app.services.feed_import._check_host"),
        patch("http.client.HTTPSConnection") as mock_cls,
    ):
        conn = MagicMock()
        mock_cls.return_value = conn
        conn.getresponse.return_value = _mock_response(404, b"")
        with pytest.raises(FeedImportError, match="feed fetch failed"):
            _fetch_feed_bytes("https://example.com/feed.xml")


def test_fetch_feed_bytes_follows_one_redirect() -> None:
    redirect_resp = _mock_response(301, b"", location="https://example.com/new.xml")
    final_resp = _mock_response(200, b"<rss/>")

    with (
        patch("app.services.feed_import._check_host"),
        patch("http.client.HTTPSConnection") as mock_cls,
    ):
        conn = MagicMock()
        mock_cls.return_value = conn
        conn.getresponse.side_effect = [redirect_resp, final_resp]
        result = _fetch_feed_bytes("https://example.com/feed.xml")
    assert result == b"<rss/>"


def test_fetch_feed_bytes_raises_on_double_redirect() -> None:
    redirect1 = _mock_response(301, b"", location="https://example.com/hop1.xml")
    redirect2 = _mock_response(302, b"", location="https://example.com/hop2.xml")

    with (
        patch("app.services.feed_import._check_host"),
        patch("http.client.HTTPSConnection") as mock_cls,
    ):
        conn = MagicMock()
        mock_cls.return_value = conn
        conn.getresponse.side_effect = [redirect1, redirect2]
        with pytest.raises(FeedImportError, match="too many redirects"):
            _fetch_feed_bytes("https://example.com/feed.xml")


def test_fetch_feed_bytes_redirect_to_non_http_scheme_rejected() -> None:
    redirect_resp = _mock_response(301, b"", location="ftp://evil.com/feed.xml")

    with (
        patch("app.services.feed_import._check_host"),
        patch("http.client.HTTPSConnection") as mock_cls,
    ):
        conn = MagicMock()
        mock_cls.return_value = conn
        conn.getresponse.return_value = redirect_resp
        with pytest.raises(FeedImportError, match="non-http scheme"):
            _fetch_feed_bytes("https://example.com/feed.xml")


# ---------------------------------------------------------------------------
# _parse_feed — RSS
# ---------------------------------------------------------------------------

RSS_FEED = textwrap.dedent("""\
    <?xml version="1.0"?>
    <rss version="2.0">
      <channel>
        <title>Test Podcast</title>
        <link>https://example.com</link>
        <image><url>https://example.com/art.jpg</url></image>
        <item>
          <title>Episode 1</title>
          <link>https://example.com/ep1</link>
          <pubDate>Mon, 01 Jan 2024 00:00:00 +0000</pubDate>
          <description>First ep</description>
        </item>
        <item>
          <title>Episode 2</title>
          <link>https://example.com/ep2</link>
          <pubDate>Tue, 02 Jan 2024 00:00:00 +0000</pubDate>
        </item>
      </channel>
    </rss>
""").encode()


RSS_FEED_WITH_DESCRIPTION = textwrap.dedent("""\
    <?xml version="1.0"?>
    <rss version="2.0">
      <channel>
        <title>Described Podcast</title>
        <link>https://example.com</link>
        <description>A great podcast about things.</description>
        <item>
          <title>Episode 1</title>
          <link>https://example.com/ep1</link>
          <pubDate>Mon, 01 Jan 2024 00:00:00 +0000</pubDate>
        </item>
      </channel>
    </rss>
""").encode()


def test_parse_feed_rss_description() -> None:
    result = _parse_feed(RSS_FEED_WITH_DESCRIPTION)
    assert result.description == "A great podcast about things."


def test_parse_feed_rss_description_absent_is_none() -> None:
    result = _parse_feed(RSS_FEED)
    assert result.description is None


def test_parse_feed_rss_title_and_website() -> None:
    result = _parse_feed(RSS_FEED)
    assert result.title == "Test Podcast"
    assert result.website == "https://example.com"


def test_parse_feed_rss_logo_url() -> None:
    result = _parse_feed(RSS_FEED)
    assert result.logo_url == "https://example.com/art.jpg"


def test_parse_feed_rss_episodes() -> None:
    result = _parse_feed(RSS_FEED)
    assert len(result.episodes) == 2
    assert result.episodes[0].title == "Episode 1"
    assert result.episodes[0].episode_url == "https://example.com/ep1"
    assert result.episodes[0].description == "First ep"
    assert result.episodes[1].title == "Episode 2"


# ---------------------------------------------------------------------------
# _parse_feed — Atom
# ---------------------------------------------------------------------------

ATOM_FEED = textwrap.dedent("""\
    <?xml version="1.0"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <title>Atom Podcast</title>
      <link rel="alternate" href="https://atom.example.com"/>
      <entry>
        <title>Atom Ep 1</title>
        <link rel="alternate" href="https://atom.example.com/ep1"/>
        <updated>2024-03-15T10:00:00Z</updated>
        <summary>Summary here</summary>
      </entry>
    </feed>
""").encode()


ATOM_FEED_WITH_SUBTITLE = textwrap.dedent("""\
    <?xml version="1.0"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <title>Subtitled Podcast</title>
      <subtitle>A great atom podcast.</subtitle>
      <link rel="alternate" href="https://atom.example.com"/>
      <entry>
        <title>Ep 1</title>
        <link rel="alternate" href="https://atom.example.com/ep1"/>
        <updated>2024-03-15T10:00:00Z</updated>
      </entry>
    </feed>
""").encode()


def test_parse_feed_atom_description_from_subtitle() -> None:
    result = _parse_feed(ATOM_FEED_WITH_SUBTITLE)
    assert result.description == "A great atom podcast."


def test_parse_feed_atom_description_absent_is_none() -> None:
    result = _parse_feed(ATOM_FEED)
    assert result.description is None


def test_parse_feed_atom_title_and_website() -> None:
    result = _parse_feed(ATOM_FEED)
    assert result.title == "Atom Podcast"
    assert result.website == "https://atom.example.com"


def test_parse_feed_atom_episodes() -> None:
    result = _parse_feed(ATOM_FEED)
    assert len(result.episodes) == 1
    assert result.episodes[0].title == "Atom Ep 1"
    assert result.episodes[0].episode_url == "https://atom.example.com/ep1"
    assert result.episodes[0].description == "Summary here"


RSS_ITUNES_IMAGE_FEED = textwrap.dedent("""\
    <?xml version="1.0"?>
    <rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
      <channel>
        <title>iTunes Podcast</title>
        <link>https://example.com</link>
        <itunes:image href="https://example.com/itunes-art.jpg"/>
        <item>
          <title>Episode 1</title>
          <link>https://example.com/ep1</link>
          <pubDate>Mon, 01 Jan 2024 00:00:00 +0000</pubDate>
        </item>
      </channel>
    </rss>
""").encode()


def test_parse_feed_rss_itunes_image_href() -> None:
    result = _parse_feed(RSS_ITUNES_IMAGE_FEED)
    assert result.logo_url == "https://example.com/itunes-art.jpg"


ATOM_WITH_LOGO_FEED = textwrap.dedent("""\
    <?xml version="1.0"?>
    <feed xmlns="http://www.w3.org/2005/Atom"
          xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
      <title>Atom Podcast With Logo</title>
      <link rel="alternate" href="https://atom.example.com"/>
      <itunes:image href="https://atom.example.com/logo.jpg"/>
      <entry>
        <title>Ep 1</title>
        <link rel="alternate" href="https://atom.example.com/ep1"/>
        <updated>2024-03-15T10:00:00Z</updated>
      </entry>
    </feed>
""").encode()


def test_parse_feed_atom_logo_url() -> None:
    result = _parse_feed(ATOM_WITH_LOGO_FEED)
    assert result.logo_url == "https://atom.example.com/logo.jpg"


# ---------------------------------------------------------------------------
# _parse_feed — error cases
# ---------------------------------------------------------------------------


def test_parse_feed_raises_on_unsupported_root() -> None:
    xml = b"<podcast><title>x</title></podcast>"
    with pytest.raises(FeedImportError, match="unsupported feed format"):
        _parse_feed(xml)


def test_parse_feed_raises_on_rss_missing_channel() -> None:
    xml = b"<rss version='2.0'></rss>"
    with pytest.raises(FeedImportError, match="rss missing channel"):
        _parse_feed(xml)


def test_parse_feed_raises_on_malformed_xml() -> None:
    import xml.etree.ElementTree as ET

    with pytest.raises((FeedImportError, ET.ParseError)):
        _parse_feed(b"<not valid xml")
