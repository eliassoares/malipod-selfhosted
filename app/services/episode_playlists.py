from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError

from app.core.placeholders import resolve_image_url
from app.core.time_format import format_duration_short
from app.db.models.podcast import (
    EpisodeActionEventModel,
    EpisodeModel,
    EpisodePlaylistItemModel,
    EpisodePlaylistModel,
    FavoriteEpisodeModel,
    PodcastFeedModel,
)
from app.schemas.episode_playlists import (
    EpisodePlaylistCard,
    EpisodePlaylistDetailPayload,
    PlaylistEpisodeRow,
    PlaylistSearchResultRow,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.core.config import Settings
    from app.db.models.user import UserModel


class EpisodePlaylistsError(Exception):
    def __init__(
        self,
        code: Literal[
            "playlist_not_found",
            "favorites_read_only",
            "title_conflict",
            "invalid_title",
            "invalid_description",
            "image_too_large",
            "invalid_image",
        ],
    ) -> None:
        self.code = code
        super().__init__(code)


@dataclass(slots=True)
class PlaylistWritePayload:
    title: str
    description: str | None
    # None means "keep existing image"; empty string means "clear image"
    image_url: str | None


def _normalize_title(value: str) -> str:
    cleaned = value.strip()
    if not cleaned or len(cleaned) > 255:
        raise EpisodePlaylistsError("invalid_title")
    return cleaned


def _normalize_description(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    if len(cleaned) > 1024:
        raise EpisodePlaylistsError("invalid_description")
    return cleaned


# Magic bytes for image format validation
_IMAGE_MAGIC: dict[str, bytes] = {
    "image/png": b"\x89PNG\r\n\x1a\n",
    "image/jpeg": b"\xff\xd8\xff",
}


def _validate_magic(content_type: str, raw: bytes) -> bool:
    magic = _IMAGE_MAGIC.get(content_type)
    if magic is None:
        if content_type == "image/webp":
            return len(raw) >= 12 and raw[:4] == b"RIFF" and raw[8:12] == b"WEBP"
        return len(raw) > 0
    return len(raw) >= len(magic) and raw[: len(magic)] == magic


class EpisodePlaylistsService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings

    async def _fetch_playlist(
        self, statement: Select[tuple[EpisodePlaylistModel]]
    ) -> EpisodePlaylistModel | None:
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_playlist(
        self, user: UserModel, playlist_id: int
    ) -> EpisodePlaylistModel:
        playlist = await self._fetch_playlist(
            select(EpisodePlaylistModel).where(
                EpisodePlaylistModel.id == playlist_id,
                EpisodePlaylistModel.user_id == user.id,
            )
        )
        if playlist is None:
            raise EpisodePlaylistsError("playlist_not_found")
        return playlist

    async def list_cards(self, user: UserModel) -> list[EpisodePlaylistCard]:
        playlists = (
            (
                await self.session.execute(
                    select(EpisodePlaylistModel)
                    .where(EpisodePlaylistModel.user_id == user.id)
                    .order_by(EpisodePlaylistModel.created_at.desc())
                )
            )
            .scalars()
            .all()
        )

        playlist_ids = [p.id for p in playlists]
        counts = await self._batch_count_items(playlist_ids)
        metrics = await self._batch_metrics(user, playlist_ids=playlist_ids)

        favorites = await self._build_favorites_card(user)
        cards: list[EpisodePlaylistCard] = [favorites]
        for playlist in playlists:
            pid = playlist.id
            episode_count = counts.get(pid, 0)
            listened_seconds, total_seconds = metrics.get(pid, (0, 0))
            cards.append(
                EpisodePlaylistCard(
                    playlist_id=pid,
                    is_favorites=False,
                    title=playlist.title,
                    description=playlist.description,
                    image_url=resolve_image_url(playlist.image_url),
                    created_at=_as_aware(playlist.created_at),
                    episode_count=episode_count,
                    listened_seconds=listened_seconds,
                    total_seconds=total_seconds,
                    listened_formatted=format_duration_short(listened_seconds),
                    total_formatted=format_duration_short(total_seconds),
                )
            )
        return cards

    async def list_user_playlists(self, user: UserModel) -> list[tuple[int, str]]:
        rows = (
            await self.session.execute(
                select(EpisodePlaylistModel.id, EpisodePlaylistModel.title)
                .where(EpisodePlaylistModel.user_id == user.id)
                .order_by(EpisodePlaylistModel.created_at.desc())
            )
        ).all()
        return [(int(pid), title) for pid, title in rows]

    async def _build_favorites_card(self, user: UserModel) -> EpisodePlaylistCard:
        count_statement = select(func.count(FavoriteEpisodeModel.id)).where(
            FavoriteEpisodeModel.user_id == user.id
        )
        raw_count = (await self.session.execute(count_statement)).scalar_one()
        episode_count = int(raw_count or 0)
        listened_seconds, total_seconds = await self._favorites_metrics(user)
        # Stable seed so the placeholder doesn't change on every page load
        image_url = resolve_image_url(None, seed=f"favorites-{user.id}")
        return EpisodePlaylistCard(
            playlist_id=None,
            is_favorites=True,
            title="Favorites",
            description=None,
            image_url=image_url,
            created_at=None,
            episode_count=episode_count,
            listened_seconds=listened_seconds,
            total_seconds=total_seconds,
            listened_formatted=format_duration_short(listened_seconds),
            total_formatted=format_duration_short(total_seconds),
        )

    async def _build_card_for_playlist(
        self, user: UserModel, playlist: EpisodePlaylistModel
    ) -> EpisodePlaylistCard:
        counts = await self._batch_count_items([playlist.id])
        metrics = await self._batch_metrics(user, playlist_ids=[playlist.id])
        episode_count = counts.get(playlist.id, 0)
        listened_seconds, total_seconds = metrics.get(playlist.id, (0, 0))
        return EpisodePlaylistCard(
            playlist_id=playlist.id,
            is_favorites=False,
            title=playlist.title,
            description=playlist.description,
            image_url=resolve_image_url(playlist.image_url),
            created_at=_as_aware(playlist.created_at),
            episode_count=episode_count,
            listened_seconds=listened_seconds,
            total_seconds=total_seconds,
            listened_formatted=format_duration_short(listened_seconds),
            total_formatted=format_duration_short(total_seconds),
        )

    async def _batch_count_items(self, playlist_ids: list[int]) -> dict[int, int]:
        if not playlist_ids:
            return {}
        result = await self.session.execute(
            select(
                EpisodePlaylistItemModel.playlist_id,
                func.count(EpisodePlaylistItemModel.id).label("cnt"),
            )
            .where(EpisodePlaylistItemModel.playlist_id.in_(playlist_ids))
            .group_by(EpisodePlaylistItemModel.playlist_id)
        )
        return {int(row.playlist_id): int(row.cnt) for row in result.all()}

    async def _batch_metrics(
        self,
        user: UserModel,
        *,
        playlist_ids: list[int],
    ) -> dict[int, tuple[int, int]]:
        """Return {playlist_id: (listened_seconds, total_seconds)} in one query."""
        if not playlist_ids:
            return {}
        play_index = self._play_index_subquery(user)
        result = await self.session.execute(
            select(
                EpisodePlaylistItemModel.playlist_id,
                func.sum(play_index.c.max_pos).label("listened"),
                func.sum(play_index.c.max_total).label("total"),
            )
            .join(
                play_index,
                play_index.c.episode_id == EpisodePlaylistItemModel.episode_id,
            )
            .where(EpisodePlaylistItemModel.playlist_id.in_(playlist_ids))
            .group_by(EpisodePlaylistItemModel.playlist_id)
        )
        return {
            int(row.playlist_id): (int(row.listened or 0), int(row.total or 0))
            for row in result.all()
        }

    async def _favorites_metrics(self, user: UserModel) -> tuple[int, int]:
        play_index = self._play_index_subquery(user)
        result = await self.session.execute(
            select(play_index.c.max_pos, play_index.c.max_total)
            .join(
                FavoriteEpisodeModel,
                FavoriteEpisodeModel.episode_id == play_index.c.episode_id,
            )
            .where(FavoriteEpisodeModel.user_id == user.id)
        )
        rows = result.all()
        return (
            sum(int(row.max_pos or 0) for row in rows),
            sum(int(row.max_total or 0) for row in rows),
        )

    def _play_index_subquery(self, user: UserModel) -> Any:
        return (
            select(
                EpisodeActionEventModel.episode_id.label("episode_id"),
                func.max(EpisodeActionEventModel.position).label("max_pos"),
                func.max(EpisodeActionEventModel.total).label("max_total"),
            )
            .where(
                EpisodeActionEventModel.user_id == user.id,
                EpisodeActionEventModel.action == "play",
                EpisodeActionEventModel.position.is_not(None),
            )
            .group_by(EpisodeActionEventModel.episode_id)
            .subquery()
        )

    async def create_playlist(
        self, user: UserModel, payload: PlaylistWritePayload
    ) -> int:
        title = _normalize_title(payload.title)
        description = _normalize_description(payload.description)
        playlist = EpisodePlaylistModel(
            user_id=user.id,
            title=title,
            description=description,
            image_url=(payload.image_url or "").strip() or None,
        )
        self.session.add(playlist)
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise EpisodePlaylistsError("title_conflict") from exc
        await self.session.refresh(playlist)
        return playlist.id

    async def update_playlist(
        self,
        user: UserModel,
        playlist_id: int,
        payload: PlaylistWritePayload,
    ) -> None:
        playlist = await self.get_playlist(user, playlist_id)
        playlist.title = _normalize_title(payload.title)
        playlist.description = _normalize_description(payload.description)
        # None means "no new image uploaded — keep existing"
        if payload.image_url is not None:
            playlist.image_url = payload.image_url.strip() or None
        playlist.updated_at = datetime.now(UTC)
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise EpisodePlaylistsError("title_conflict") from exc

    async def delete_playlist(self, user: UserModel, playlist_id: int) -> None:
        playlist = await self.get_playlist(user, playlist_id)
        await self.session.delete(playlist)
        await self.session.commit()

    async def build_detail(
        self,
        user: UserModel,
        playlist_id: int,
        *,
        search_query: str | None = None,
    ) -> EpisodePlaylistDetailPayload:
        playlist = await self.get_playlist(user, playlist_id)
        card = await self._build_card_for_playlist(user, playlist)
        episodes = await self._list_playlist_episodes(playlist_id)
        results: list[PlaylistSearchResultRow] = []
        cleaned_q = (search_query or "").strip()
        if cleaned_q:
            results = await self._search_episodes_for_playlist(
                playlist_id=playlist_id,
                query=cleaned_q,
                limit=20,
            )
        return EpisodePlaylistDetailPayload(
            card=card,
            episodes=episodes,
            search_results=results,
            search_query=cleaned_q or None,
        )

    async def add_episode(
        self, user: UserModel, playlist_id: int, episode_id: int
    ) -> None:
        await self.get_playlist(user, playlist_id)
        existing = (
            await self.session.execute(
                select(EpisodePlaylistItemModel).where(
                    EpisodePlaylistItemModel.playlist_id == playlist_id,
                    EpisodePlaylistItemModel.episode_id == episode_id,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            return
        self.session.add(
            EpisodePlaylistItemModel(
                playlist_id=playlist_id,
                episode_id=episode_id,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        )
        await self.session.commit()

    async def remove_episode(
        self, user: UserModel, playlist_id: int, episode_id: int
    ) -> None:
        await self.get_playlist(user, playlist_id)
        statement = select(EpisodePlaylistItemModel).where(
            EpisodePlaylistItemModel.playlist_id == playlist_id,
            EpisodePlaylistItemModel.episode_id == episode_id,
        )
        item = (await self.session.execute(statement)).scalar_one_or_none()
        if item is None:
            return
        await self.session.delete(item)
        await self.session.commit()

    async def add_episode_to_playlists(
        self,
        user: UserModel,
        *,
        episode_id: int,
        playlist_ids: Sequence[int],
    ) -> None:
        unique_ids = sorted({pid for pid in playlist_ids if pid > 0})
        if not unique_ids:
            return
        playlists = (
            (
                await self.session.execute(
                    select(EpisodePlaylistModel).where(
                        EpisodePlaylistModel.user_id == user.id,
                        EpisodePlaylistModel.id.in_(unique_ids),
                    )
                )
            )
            .scalars()
            .all()
        )
        allowed_ids = {p.id for p in playlists}
        if not allowed_ids:
            return

        # Pre-check existing memberships to avoid IntegrityError on commit
        existing_result = await self.session.execute(
            select(EpisodePlaylistItemModel.playlist_id).where(
                EpisodePlaylistItemModel.episode_id == episode_id,
                EpisodePlaylistItemModel.playlist_id.in_(allowed_ids),
            )
        )
        existing_ids = {int(row[0]) for row in existing_result.all()}

        now = datetime.now(UTC)
        for playlist_id in unique_ids:
            if playlist_id not in allowed_ids or playlist_id in existing_ids:
                continue
            self.session.add(
                EpisodePlaylistItemModel(
                    playlist_id=playlist_id,
                    episode_id=episode_id,
                    created_at=now,
                    updated_at=now,
                )
            )
        await self.session.commit()

    async def save_image_upload(
        self,
        user: UserModel,
        *,
        content_type: str | None,
        raw: bytes,
    ) -> str:
        if len(raw) > 1 * 1024 * 1024:
            raise EpisodePlaylistsError("image_too_large")
        if not raw:
            raise EpisodePlaylistsError("invalid_image")
        cleaned_type = (content_type or "").lower().strip()
        if not cleaned_type.startswith("image/"):
            raise EpisodePlaylistsError("invalid_image")
        if not _validate_magic(cleaned_type, raw):
            raise EpisodePlaylistsError("invalid_image")
        ext = _guess_extension(cleaned_type)
        filename = f"{secrets.token_urlsafe(16)}{ext}"
        url = f"/static/uploads/playlists/{user.id}/{filename}"
        if self.settings.environment == "test":
            return url
        target = Path("app/static/uploads/playlists") / str(user.id)
        target.mkdir(parents=True, exist_ok=True)
        (target / filename).write_bytes(raw)
        return url

    async def _list_playlist_episodes(
        self, playlist_id: int
    ) -> list[PlaylistEpisodeRow]:
        statement = (
            select(EpisodeModel, PodcastFeedModel.title)
            .join(
                EpisodePlaylistItemModel,
                EpisodePlaylistItemModel.episode_id == EpisodeModel.id,
            )
            .join(PodcastFeedModel, PodcastFeedModel.id == EpisodeModel.feed_id)
            .where(EpisodePlaylistItemModel.playlist_id == playlist_id)
            .order_by(EpisodePlaylistItemModel.created_at.desc())
        )
        rows = (await self.session.execute(statement)).all()
        return [
            PlaylistEpisodeRow(
                episode_id=episode.id,
                title=episode.title,
                podcast_title=podcast_title,
                released_at=_as_aware(episode.released_at),
                logo_url=resolve_image_url(episode.logo_url, seed=episode.episode_url),
            )
            for episode, podcast_title in rows
        ]

    async def _search_episodes_for_playlist(
        self,
        *,
        playlist_id: int,
        query: str,
        limit: int,
    ) -> list[PlaylistSearchResultRow]:
        candidate = f"%{query}%"
        in_playlist = (
            select(EpisodePlaylistItemModel.episode_id)
            .where(EpisodePlaylistItemModel.playlist_id == playlist_id)
            .subquery()
        )
        statement = (
            select(
                EpisodeModel,
                PodcastFeedModel.title,
                in_playlist.c.episode_id.is_not(None).label("is_in_playlist"),
            )
            .join(PodcastFeedModel, PodcastFeedModel.id == EpisodeModel.feed_id)
            .outerjoin(in_playlist, in_playlist.c.episode_id == EpisodeModel.id)
            .where(
                EpisodeModel.title.ilike(candidate)
                | PodcastFeedModel.title.ilike(candidate)
            )
            .order_by(EpisodeModel.released_at.desc())
            .limit(limit)
        )
        rows = (await self.session.execute(statement)).all()
        return [
            PlaylistSearchResultRow(
                episode_id=episode.id,
                title=episode.title,
                podcast_title=podcast_title,
                released_at=_as_aware(episode.released_at),
                logo_url=resolve_image_url(episode.logo_url, seed=episode.episode_url),
                is_in_playlist=bool(is_in),
            )
            for episode, podcast_title, is_in in rows
        ]


def _guess_extension(content_type: str) -> str:
    if content_type == "image/png":
        return ".png"
    if content_type in {"image/jpeg", "image/jpg"}:
        return ".jpg"
    if content_type == "image/webp":
        return ".webp"
    return ".img"


def _as_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value
