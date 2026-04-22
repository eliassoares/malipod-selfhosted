from __future__ import annotations

from app.services.feed_import import _parse_feed


def test_parse_rss_includes_author_categories_and_episode_logo() -> None:
    xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" version="2.0">
  <channel>
    <title>Example Feed</title>
    <link>https://example.com</link>
    <description>Example description</description>
    <itunes:author>Jane Doe</itunes:author>
    <itunes:category text="Technology">
      <itunes:category text="Gadgets" />
    </itunes:category>
    <category>News</category>
    <item>
      <title>Episode 1</title>
      <link>https://example.com/ep1</link>
      <pubDate>Wed, 22 Apr 2026 12:00:00 GMT</pubDate>
      <itunes:image href="https://example.com/ep1.png" />
    </item>
  </channel>
</rss>
"""
    parsed = _parse_feed(xml)
    assert parsed.author == "Jane Doe"
    assert parsed.categories == ["Technology", "Gadgets", "News"]
    assert parsed.episodes[0].logo_url == "https://example.com/ep1.png"


def test_parse_atom_includes_author_and_categories() -> None:
    xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Atom Feed</title>
  <subtitle>Atom description</subtitle>
  <author><name>Alice</name></author>
  <link rel="alternate" href="https://example.com" />
  <category term="Tech" />
  <entry>
    <title>Entry 1</title>
    <updated>2026-04-22T12:00:00Z</updated>
    <link rel="alternate" href="https://example.com/entry1" />
    <logo>https://example.com/entry1.png</logo>
  </entry>
</feed>
"""
    parsed = _parse_feed(xml)
    assert parsed.author == "Alice"
    assert parsed.categories == ["Tech"]
    assert parsed.episodes[0].logo_url == "https://example.com/entry1.png"
