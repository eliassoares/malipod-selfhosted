from __future__ import annotations

from app.services.feed_import import _parse_feed


def test_parse_rss_enclosure_url_as_media_url() -> None:
    xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Example Feed</title>
    <item>
      <title>Episode 1</title>
      <link>https://example.com/ep1</link>
      <pubDate>Wed, 22 Apr 2026 12:00:00 GMT</pubDate>
      <enclosure url="https://cdn.example.com/ep1.mp3" type="audio/mpeg" />
    </item>
  </channel>
</rss>
"""
    parsed = _parse_feed(xml)
    assert parsed.episodes[0].media_url == "https://cdn.example.com/ep1.mp3"


def test_parse_atom_enclosure_link_as_media_url() -> None:
    xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Atom Feed</title>
  <entry>
    <title>Entry 1</title>
    <updated>2026-04-22T12:00:00Z</updated>
    <link rel="alternate" href="https://example.com/entry1" />
    <link rel="enclosure" href="https://cdn.example.com/entry1.mp3" />
  </entry>
</feed>
"""
    parsed = _parse_feed(xml)
    assert parsed.episodes[0].media_url == "https://cdn.example.com/entry1.mp3"
