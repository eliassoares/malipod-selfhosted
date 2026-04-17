from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models.podcast import EpisodeModel, FavoriteEpisodeModel
from app.db.models.user import UserModel
from app.schemas.favorite import FavoriteEpisodeItem

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class FavoritesError(Exception):
    def __init__(self, code: Literal["forbidden", "target_not_found"]) -> None:
        self.code = code
        super().__init__(code)


class FavoritesService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _get_target_user(self, username: str) -> UserModel | None:
        result = await self.session.execute(
            select(UserModel).where(
                UserModel.nickname == username,
                UserModel.deactivated_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_favorites(
        self,
        authenticated_user: UserModel,
        *,
        username: str,
    ) -> list[FavoriteEpisodeItem]:
        if authenticated_user.nickname != username:
            target_user = await self._get_target_user(username)
            if target_user is None:
                raise FavoritesError("target_not_found")
            # 404 before 403: gpodder.net returns not-found for absent users even
            # to authenticated callers; 403 only when the target account exists.
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
