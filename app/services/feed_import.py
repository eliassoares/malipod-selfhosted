from __future__ import annotations

import asyncio
import http.client
import ipaddress
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


class Element(Protocol):
    tag: str
    text: str | None
    attrib: dict[str, str]

    def __iter__(self) -> Iterator[Element]: ...


class FeedImportError(Exception):
    pass


def _is_public_address(hostname: str) -> bool:
    if hostname.lower() in {"localhost"}:
        return False
    try:
        infos = socket.getaddrinfo(hostname, None)
    except OSError:
        return False
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
            return False
    return True


def _fetch_feed_bytes(url: str) -> bytes:
    parsed = urlsplit(url)
    if not parsed.hostname or not _is_public_address(parsed.hostname):
        raise FeedImportError("invalid host")
    if parsed.scheme.lower() not in {"http", "https"}:
        raise FeedImportError("unsupported scheme")

    host = parsed.hostname
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
        if 300 <= response.status < 400:
            raise FeedImportError("redirects are not allowed")
        if response.status >= 400:
            raise FeedImportError("feed fetch failed")

        max_bytes = 5 * 1024 * 1024
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
        return b"".join(chunks)
    except (OSError, http.client.HTTPException) as exc:
        raise FeedImportError("feed fetch failed") from exc
    finally:
        connection.close()


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


def _parse_rss(channel: Element) -> ParsedFeed:
    title = _find_child_text(channel, "title")
    website = _find_child_text(channel, "link")

    logo_url: str | None = None
    for child in channel:
        if _strip_ns(child.tag) == "image":
            logo_url = _find_child_text(child, "url")
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
        description = _find_child_text(child, "description")
        episodes.append(
            ParsedEpisode(
                episode_url=episode_url,
                title=item_title,
                released_at=published,
                description=description,
                website=episode_url,
            )
        )
        if len(episodes) >= 200:
            break

    return ParsedFeed(
        title=title,
        website=website,
        logo_url=logo_url,
        episodes=episodes,
    )


def _parse_atom(feed: Element) -> ParsedFeed:
    title = _find_child_text(feed, "title")
    website = None
    for child in feed:
        if _strip_ns(child.tag) != "link":
            continue
        href = child.attrib.get("href")
        rel = (child.attrib.get("rel") or "").lower()
        if rel in {"alternate", ""} and href:
            website = href.strip()
            break

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
        episodes.append(
            ParsedEpisode(
                episode_url=episode_url,
                title=item_title,
                released_at=published,
                description=_find_child_text(child, "summary"),
                website=episode_url,
            )
        )
        if len(episodes) >= 200:
            break

    return ParsedFeed(title=title, website=website, logo_url=None, episodes=episodes)


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
                description=None,
                website=parsed.website,
                logo_url=parsed.logo_url or choose_placeholder_url_random(),
                mygpo_link=None,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            self.session.add(feed_row)
            await self.session.flush()
        else:
            if parsed.title:
                feed_row.title = parsed.title
            if parsed.website:
                feed_row.website = parsed.website
            if parsed.logo_url:
                feed_row.logo_url = parsed.logo_url
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
        return
