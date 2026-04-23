from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.placeholders import choose_placeholder_url_stable
from app.db.models.podcast import (
    EpisodeActionEventModel,
    EpisodeActionModel,
    EpisodeModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db.models.user import UserModel


@dataclass(slots=True)
class EpisodeProgress:
    position: int | None
    total: int | None
    occurred_at: datetime | None


@dataclass(slots=True)
class ListeningEvent:
    action: str
    occurred_at: datetime


def _normalize_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


class EpisodeDetailService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_episode(self, *, episode_id: int) -> EpisodeModel | None:
        result = await self.session.execute(
            select(EpisodeModel)
            .options(selectinload(EpisodeModel.feed))
            .where(EpisodeModel.id == episode_id)
        )
        return result.scalar_one_or_none()

    async def get_progress(
        self, user: UserModel, *, episode_id: int
    ) -> EpisodeProgress:
        result = await self.session.execute(
            select(EpisodeActionModel).where(
                EpisodeActionModel.user_id == user.id,
                EpisodeActionModel.episode_id == episode_id,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            return EpisodeProgress(position=None, total=None, occurred_at=None)
        payload = row.action or {}
        position = payload.get("position")
        total = payload.get("total")
        occurred_at = _normalize_timestamp(row.occurred_at)
        return EpisodeProgress(
            position=int(position) if isinstance(position, int) else None,
            total=int(total) if isinstance(total, int) else None,
            occurred_at=occurred_at,
        )

    async def list_recent_history(
        self,
        user: UserModel,
        *,
        episode_id: int,
        limit: int = 20,
    ) -> list[ListeningEvent]:
        statement = (
            select(EpisodeActionEventModel)
            .where(
                EpisodeActionEventModel.user_id == user.id,
                EpisodeActionEventModel.episode_id == episode_id,
            )
            .order_by(
                EpisodeActionEventModel.occurred_at.desc(),
                EpisodeActionEventModel.id.desc(),
            )
            .limit(limit)
        )
        result = await self.session.execute(statement)
        rows = result.scalars().all()
        events: list[ListeningEvent] = []
        for row in rows:
            events.append(
                ListeningEvent(
                    action=row.action,
                    occurred_at=_normalize_timestamp(row.occurred_at),
                )
            )
        return events

    @staticmethod
    def choose_episode_logo_url(episode: EpisodeModel) -> str:
        return (episode.logo_url or "").strip() or choose_placeholder_url_stable(
            episode.episode_url
        )
