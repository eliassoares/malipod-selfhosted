from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.models.podcast import FavoritePodcastModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db.models.user import UserModel


class PodcastFavoritesService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def is_favorited(self, user: UserModel, *, feed_id: int) -> bool:
        result = await self.session.execute(
            select(FavoritePodcastModel.id).where(
                FavoritePodcastModel.user_id == user.id,
                FavoritePodcastModel.feed_id == feed_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def list_favorite_feed_ids(self, user: UserModel) -> set[int]:
        result = await self.session.execute(
            select(FavoritePodcastModel.feed_id).where(
                FavoritePodcastModel.user_id == user.id
            )
        )
        return set(result.scalars().all())

    async def toggle_favorite(self, user: UserModel, *, feed_id: int) -> bool:
        result = await self.session.execute(
            select(FavoritePodcastModel).where(
                FavoritePodcastModel.user_id == user.id,
                FavoritePodcastModel.feed_id == feed_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            await self.session.delete(existing)
            await self.session.commit()
            return False

        now = datetime.now(UTC)
        self.session.add(
            FavoritePodcastModel(
                user_id=user.id,
                feed_id=feed_id,
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
