from __future__ import annotations

from pydantic import AwareDatetime, BaseModel


class SubscriptionFeedCard(BaseModel):
    title: str
    feed_url: str
    logo_url: str
    episode_count: int
    last_episode_at: AwareDatetime | None
