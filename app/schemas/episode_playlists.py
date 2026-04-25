from __future__ import annotations

from pydantic import AwareDatetime, BaseModel


class EpisodePlaylistCard(BaseModel):
    playlist_id: int | None
    is_favorites: bool = False
    title: str
    description: str | None
    image_url: str
    created_at: AwareDatetime | None = None
    episode_count: int
    listened_seconds: int = 0
    total_seconds: int = 0
    listened_formatted: str = "0s"
    total_formatted: str = "0s"


class PlaylistEpisodeRow(BaseModel):
    episode_id: int
    title: str
    podcast_title: str
    released_at: AwareDatetime
    logo_url: str
    is_in_playlist: bool = True


class PlaylistSearchResultRow(BaseModel):
    episode_id: int
    title: str
    podcast_title: str
    released_at: AwareDatetime
    logo_url: str
    is_in_playlist: bool


class EpisodePlaylistDetailPayload(BaseModel):
    card: EpisodePlaylistCard
    episodes: list[PlaylistEpisodeRow]
    search_results: list[PlaylistSearchResultRow] = []
    search_query: str | None = None
