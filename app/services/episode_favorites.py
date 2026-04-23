from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.models.podcast import FavoriteEpisodeModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db.models.user import UserModel


class EpisodeFavoritesService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def is_favorited(self, user: UserModel, *, episode_id: int) -> bool:
        result = await self.session.execute(
            select(FavoriteEpisodeModel.id).where(
                FavoriteEpisodeModel.user_id == user.id,
                FavoriteEpisodeModel.episode_id == episode_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def toggle_favorite(self, user: UserModel, *, episode_id: int) -> bool:
        result = await self.session.execute(
            select(FavoriteEpisodeModel).where(
                FavoriteEpisodeModel.user_id == user.id,
                FavoriteEpisodeModel.episode_id == episode_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            await self.session.delete(existing)
            await self.session.commit()
            return False

        now = datetime.now(UTC)
        self.session.add(
            FavoriteEpisodeModel(
                user_id=user.id,
                episode_id=episode_id,
                favorited_at=now,
                created_at=now,
                updated_at=now,
            )
        )
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
        return True
