from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models.podcast import EpisodeModel, FavoriteEpisodeModel
from app.schemas.favorite import FavoriteEpisodeItem

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db.models.user import UserModel


class FavoritesError(Exception):
    def __init__(self, code: Literal["forbidden"]) -> None:
        self.code = code
        super().__init__(code)


class FavoritesService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_favorites(
        self,
        authenticated_user: UserModel,
        *,
        username: str,
    ) -> list[FavoriteEpisodeItem]:
        # Always 403 for any cross-account request — avoids leaking whether a
        # username exists to other authenticated users.
        if authenticated_user.nickname != username:
            raise FavoritesError("forbidden")

        result = await self.session.execute(
            select(FavoriteEpisodeModel)
            .options(
                selectinload(FavoriteEpisodeModel.episode).selectinload(
                    EpisodeModel.feed
                )
            )
            .where(FavoriteEpisodeModel.user_id == authenticated_user.id)
            .order_by(
                FavoriteEpisodeModel.favorited_at.desc(),
                FavoriteEpisodeModel.episode_id.asc(),
            )
        )
        favorites = result.scalars().all()
        return [
            FavoriteEpisodeItem(
                title=favorite.episode.title,
                url=favorite.episode.episode_url,
                podcast_title=favorite.episode.feed.title,
                podcast_url=favorite.episode.feed.feed_url,
                description=favorite.episode.description,
                website=favorite.episode.website,
                released=favorite.episode.released_at,
                mygpo_link=favorite.episode.mygpo_link,
            )
            for favorite in favorites
        ]
