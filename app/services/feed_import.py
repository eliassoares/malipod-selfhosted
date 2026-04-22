from __future__ import annotations

import asyncio
import http.client
import ipaddress
import logging
import socket
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import TYPE_CHECKING, Protocol
from urllib.parse import urlsplit

from sqlalchemy import select

from app.core.placeholders import choose_placeholder_url_random
from app.core.security import sanitize_subscription_url
from app.db.models.podcast import EpisodeModel, PodcastFeedModel
from app.db.session import get_session_factory

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.core.config import Settings

logger = logging.getLogger(__name__)


class Element(Protocol):
    tag: str
    text: str | None
    attrib: dict[str, str]

    def __iter__(self) -> Iterator[Element]: ...


class FeedImportError(Exception):
    pass


def _check_host(hostname: str) -> None:
    """Raise FeedImportError if hostname is missing, private, or unresolvable."""
    if not hostname or hostname.lower() == "localhost":
        raise FeedImportError("invalid host")
    try:
        infos = socket.getaddrinfo(hostname, None)
    except OSError as exc:
        raise FeedImportError("dns resolution failed") from exc
    for info in infos:
        addr = info[4][0]
        ip = ipaddress.ip_address(addr)
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
        ):
            raise FeedImportError("invalid host")


def _fetch_one(url: str) -> tuple[int, str | None, bytes]:
    """Fetch url, return (status, location_header, body_bytes)."""
    parsed = urlsplit(url)
    _check_host(parsed.hostname or "")
    if parsed.scheme.lower() not in {"http", "https"}:
        raise FeedImportError("unsupported scheme")

    host: str = parsed.hostname or ""
    port = parsed.port
    target = parsed.path or "/"
    if parsed.query:
        target = f"{target}?{parsed.query}"

    connection_cls: type[http.client.HTTPConnection]
    if parsed.scheme.lower() == "https":
        connection_cls = http.client.HTTPSConnection
    else:
        connection_cls = http.client.HTTPConnection

    connection = connection_cls(host, port=port, timeout=10)
    try:
        connection.request(
            "GET",
            target,
            headers={
                "User-Agent": "malipod/0.1",
                "Accept": (
                    "application/rss+xml, application/atom+xml, application/xml, "
                    "text/xml, */*"
                ),
                "Host": host,
            },
        )
        response = connection.getresponse()
        location = response.getheader("Location")
        if response.status >= 400:
            raise FeedImportError("feed fetch failed")

        max_bytes = 25 * 1024 * 1024
        chunks: list[bytes] = []
        read = 0
        while True:
            chunk = response.read(64 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
            read += len(chunk)
            if read > max_bytes:
                raise FeedImportError("feed too large")
        return response.status, location, b"".join(chunks)
    except (OSError, http.client.HTTPException) as exc:
        raise FeedImportError("feed fetch failed") from exc
    finally:
        connection.close()


def _fetch_feed_bytes(url: str) -> bytes:
    status, location, body = _fetch_one(url)
    if 300 <= status < 400:
        if not location:
            raise FeedImportError("redirect with no Location header")
        parsed_redirect = urlsplit(location)
        if parsed_redirect.scheme.lower() not in {"http", "https"}:
            raise FeedImportError("redirect to non-http scheme")
        status2, _location2, body2 = _fetch_one(location)
        if 300 <= status2 < 400:
            raise FeedImportError("too many redirects")
        return body2
    return body


def _strip_ns(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _find_child_text(element: Element, name: str) -> str | None:
    for child in element:
        if _strip_ns(child.tag) == name:
            if child.text:
                return child.text.strip()
            return None
    return None


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    candidate = value.strip()
    try:
        parsed = parsedate_to_datetime(candidate)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed
    except (TypeError, ValueError):
        return None


@dataclass(slots=True)
class ParsedEpisode:
    episode_url: str
    title: str
    released_at: datetime
    description: str | None = None
    website: str | None = None
    logo_url: str | None = None


@dataclass(slots=True)
class ParsedFeed:
    title: str | None
    website: str | None
    logo_url: str | None
    episodes: list[ParsedEpisode]
    description: str | None = None
    author: str | None = None
    categories: list[str] | None = None


def _dedupe_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in values:
        cleaned = raw.strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        out.append(cleaned)
    return out


def _collect_itunes_categories(element: Element, out: list[str]) -> None:
    candidate = (element.attrib.get("text") or "").strip()
    if candidate:
        out.append(candidate)
    for child in element:
        if _strip_ns(child.tag) == "category":
            _collect_itunes_categories(child, out)


def _parse_rss(channel: Element) -> ParsedFeed:
    title = _find_child_text(channel, "title")
    website = _find_child_text(channel, "link")
    description = _find_child_text(channel, "description")
    author = (
        _find_child_text(channel, "author")
        or _find_child_text(channel, "managingEditor")
        or _find_child_text(channel, "creator")
    )

    raw_categories: list[str] = []
    for child in channel:
        if _strip_ns(child.tag) != "category":
            continue
        if child.attrib.get("text"):
            _collect_itunes_categories(child, raw_categories)
        elif child.text:
            raw_categories.append(child.text)
    categories = _dedupe_strings(raw_categories) or None

    logo_url: str | None = None
    for child in channel:
        if _strip_ns(child.tag) == "image":
            candidate = _find_child_text(child, "url") or child.attrib.get("href") or ""
            candidate = candidate.strip()
            if candidate:
                logo_url = candidate
                break

    episodes: list[ParsedEpisode] = []
    for child in channel:
        if _strip_ns(child.tag) != "item":
            continue
        item_title = _find_child_text(child, "title") or "Untitled episode"
        link = _find_child_text(child, "link") or _find_child_text(child, "guid") or ""
        episode_url = link.strip()
        if not episode_url:
            continue
        published = _parse_datetime(_find_child_text(child, "pubDate")) or datetime.now(
            UTC
        )
        ep_description = _find_child_text(child, "description")
        episode_logo_url: str | None = None
        for item_child in child:
            tag = _strip_ns(item_child.tag)
            if tag != "image":
                continue
            candidate = (
                _find_child_text(item_child, "url")
                or item_child.attrib.get("href")
                or item_child.attrib.get("url")
                or ""
            )
            candidate = candidate.strip()
            if candidate:
                episode_logo_url = candidate
                break
        episodes.append(
            ParsedEpisode(
                episode_url=episode_url,
                title=item_title,
                released_at=published,
                description=ep_description,
                website=episode_url,
                logo_url=episode_logo_url,
            )
        )
        if len(episodes) >= 200:
            break

    return ParsedFeed(
        title=title,
        website=website,
        logo_url=logo_url,
        episodes=episodes,
        description=description,
        author=author,
        categories=categories,
    )


def _parse_atom(feed: Element) -> ParsedFeed:
    title = _find_child_text(feed, "title")
    description = _find_child_text(feed, "subtitle")
    website = None
    logo_url: str | None = None
    author: str | None = None
    raw_categories: list[str] = []
    for child in feed:
        tag = _strip_ns(child.tag)
        if tag == "link" and website is None:
            href = child.attrib.get("href")
            rel = (child.attrib.get("rel") or "").lower()
            if rel in {"alternate", ""} and href:
                website = href.strip()
        elif tag in {"image", "logo", "icon"} and logo_url is None:
            candidate = _find_child_text(child, "url") or child.attrib.get("href") or ""
            candidate = candidate.strip()
            if candidate:
                logo_url = candidate
        elif tag == "author" and author is None:
            author = (
                _find_child_text(child, "name") or (child.text or "").strip() or None
            )
        elif tag == "category":
            term = (child.attrib.get("term") or "").strip()
            if term:
                raw_categories.append(term)
        if website and logo_url:
            break

    categories = _dedupe_strings(raw_categories) or None

    episodes: list[ParsedEpisode] = []
    for child in feed:
        if _strip_ns(child.tag) != "entry":
            continue
        item_title = _find_child_text(child, "title") or "Untitled episode"
        link = None
        for link_el in child:
            if _strip_ns(link_el.tag) != "link":
                continue
            href = link_el.attrib.get("href")
            rel = (link_el.attrib.get("rel") or "").lower()
            if href and rel in {"alternate", ""}:
                link = href.strip()
                break
        episode_url = link or ""
        if not episode_url:
            continue
        published = _parse_datetime(_find_child_text(child, "updated")) or datetime.now(
            UTC
        )
        entry_logo_url: str | None = None
        for entry_child in child:
            tag = _strip_ns(entry_child.tag)
            if tag in {"image", "logo", "icon"}:
                candidate = (
                    _find_child_text(entry_child, "url")
                    or entry_child.attrib.get("href")
                    or (entry_child.text or "")
                ).strip()
                if candidate:
                    entry_logo_url = candidate
                    break

        episodes.append(
            ParsedEpisode(
                episode_url=episode_url,
                title=item_title,
                released_at=published,
                description=_find_child_text(child, "summary"),
                website=episode_url,
                logo_url=entry_logo_url,
            )
        )
        if len(episodes) >= 200:
            break

    return ParsedFeed(
        title=title,
        website=website,
        logo_url=logo_url,
        episodes=episodes,
        description=description,
        author=author,
        categories=categories,
    )


def _parse_feed(xml_bytes: bytes) -> ParsedFeed:
    from defusedxml import ElementTree

    root = ElementTree.fromstring(xml_bytes)
    root_tag = _strip_ns(root.tag).lower()
    if root_tag == "rss":
        for child in root:
            if _strip_ns(child.tag) == "channel":
                return _parse_rss(child)
        raise FeedImportError("rss missing channel")
    if root_tag == "feed":
        return _parse_atom(root)
    raise FeedImportError("unsupported feed format")


@dataclass(slots=True)
class FeedImportService:
    session: AsyncSession

    async def import_feed(self, feed_url: str) -> None:
        sanitized = sanitize_subscription_url(feed_url)
        if not sanitized:
            raise FeedImportError("invalid feed url")

        raw = await asyncio.to_thread(_fetch_feed_bytes, sanitized)
        parsed = _parse_feed(raw)

        feed_row = (
            await self.session.execute(
                select(PodcastFeedModel).where(PodcastFeedModel.feed_url == sanitized)
            )
        ).scalar_one_or_none()
        if feed_row is None:
            feed_row = PodcastFeedModel(
                feed_url=sanitized,
                title=parsed.title or sanitized,
                author=parsed.author,
                description=parsed.description,
                website=parsed.website,
                logo_url=parsed.logo_url or choose_placeholder_url_random(),
                mygpo_link=None,
                categories=parsed.categories,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            self.session.add(feed_row)
            await self.session.flush()
        else:
            if parsed.title:
                feed_row.title = parsed.title
            if parsed.author:
                feed_row.author = parsed.author
            if parsed.description:
                feed_row.description = parsed.description
            if parsed.website:
                feed_row.website = parsed.website
            if parsed.logo_url:
                feed_row.logo_url = parsed.logo_url
            if parsed.categories:
                feed_row.categories = parsed.categories
            feed_row.updated_at = datetime.now(UTC)
            await self.session.flush()

        for episode in parsed.episodes:
            existing = (
                await self.session.execute(
                    select(EpisodeModel).where(
                        EpisodeModel.episode_url == episode.episode_url
                    )
                )
            ).scalar_one_or_none()
            if existing is None:
                self.session.add(
                    EpisodeModel(
                        feed_id=feed_row.id,
                        episode_url=episode.episode_url,
                        title=episode.title,
                        description=episode.description,
                        website=episode.website,
                        mygpo_link=None,
                        logo_url=episode.logo_url or choose_placeholder_url_random(),
                        released_at=episode.released_at,
                        created_at=datetime.now(UTC),
                        updated_at=datetime.now(UTC),
                    )
                )
            else:
                existing.title = episode.title
                existing.description = episode.description
                existing.website = episode.website
                if episode.logo_url:
                    existing.logo_url = episode.logo_url
                existing.released_at = episode.released_at
                existing.updated_at = datetime.now(UTC)

        await self.session.commit()


async def import_feed_in_background(settings: Settings, feed_url: str) -> None:
    try:
        session_factory = get_session_factory(settings)
        async with session_factory() as session:
            await FeedImportService(session=session).import_feed(feed_url)
    except Exception:
        logger.exception("background feed import failed for %s", feed_url)
