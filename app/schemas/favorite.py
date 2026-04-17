from pydantic import AwareDatetime, BaseModel


class FavoriteEpisodeItem(BaseModel):
    title: str
    url: str
    podcast_title: str
    podcast_url: str
    description: str | None = None
    website: str | None = None
    released: AwareDatetime | None = None
    mygpo_link: str | None = None
