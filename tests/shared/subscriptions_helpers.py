from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import select

from app.db.models.device import DeviceModel
from app.db.models.podcast import (
    DeviceSubscriptionModel,
    EpisodeModel,
    PodcastFeedModel,
)
from app.db.models.user import UserModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def get_user(db_session: AsyncSession, nickname: str) -> UserModel:
    result = await db_session.execute(
        select(UserModel).where(UserModel.nickname == nickname)
    )
    user = result.scalar_one_or_none()
    assert user is not None
    return user


async def ensure_device(
    db_session: AsyncSession,
    user: UserModel,
    device_id: str = "device-1",
) -> DeviceModel:
    result = await db_session.execute(
        select(DeviceModel).where(
            DeviceModel.user_id == user.id,
            DeviceModel.device_id == device_id,
        )
    )
    device = result.scalar_one_or_none()
    if device is not None:
        return device
    now = datetime.now(UTC)
    device = DeviceModel(
        user_id=user.id,
        device_id=device_id,
        caption="",
        device_type="other",
        created_at=now,
        updated_at=now,
    )
    db_session.add(device)
    await db_session.commit()
    await db_session.refresh(device)
    return device


async def create_feed(
    db_session: AsyncSession,
    *,
    feed_url: str,
    title: str,
    logo_url: str | None = None,
) -> PodcastFeedModel:
    result = await db_session.execute(
        select(PodcastFeedModel).where(PodcastFeedModel.feed_url == feed_url)
    )
    feed = result.scalar_one_or_none()
    if feed is not None:
        return feed
    now = datetime.now(UTC)
    feed = PodcastFeedModel(
        feed_url=feed_url,
        title=title,
        author=None,
        description=None,
        website=None,
        logo_url=logo_url or "/static/placeholders/lilith.png",
        mygpo_link=None,
        categories=None,
        created_at=now,
        updated_at=now,
    )
    db_session.add(feed)
    await db_session.commit()
    await db_session.refresh(feed)
    return feed


async def subscribe(
    db_session: AsyncSession,
    *,
    device: DeviceModel,
    feed: PodcastFeedModel,
) -> None:
    now = datetime.now(UTC)
    row = DeviceSubscriptionModel(
        device_pk=device.id,
        feed_id=feed.id,
        subscribed_at=now,
        unsubscribed_at=None,
        updated_at=now,
    )
    db_session.add(row)
    await db_session.commit()


async def add_episode(
    db_session: AsyncSession,
    *,
    feed: PodcastFeedModel,
    episode_url: str,
    title: str,
    released_at: datetime | None = None,
) -> EpisodeModel:
    now = datetime.now(UTC)
    released = released_at or now
    episode = EpisodeModel(
        feed_id=feed.id,
        episode_url=episode_url,
        title=title,
        description=None,
        website=episode_url,
        mygpo_link=None,
        logo_url="/static/placeholders/malte.png",
        released_at=released,
        created_at=now,
        updated_at=now,
    )
    db_session.add(episode)
    await db_session.commit()
    await db_session.refresh(episode)
    return episode


def days_ago(days: int) -> datetime:
    return datetime.now(UTC) - timedelta(days=days)
