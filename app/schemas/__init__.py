"""Pydantic schemas for API and site views."""

from app.schemas.episode import (
    EpisodeActionInput,
    EpisodeActionOutput,
    EpisodeActionQuery,
    EpisodeActionQueryResponse,
    EpisodeActionUploadResponse,
)
from app.schemas.podcast_list import (
    PodcastListCreateRequest,
    PodcastListCreateResponse,
    PodcastListDocument,
    PodcastListEntry,
    PodcastListJsonUpload,
    PodcastListJsonUploadDocument,
    PodcastListJsonUploadItem,
    PodcastListPathRequest,
    PodcastListQuery,
    PodcastListRenderPayload,
    PodcastListRenderResult,
    PodcastListSummary,
    PodcastListUpdateRequest,
)
from app.schemas.setting import (
    SettingsDocument,
    SettingsMutationRequest,
    SettingsScopeQuery,
)

__all__ = [
    "EpisodeActionInput",
    "EpisodeActionOutput",
    "EpisodeActionQuery",
    "EpisodeActionQueryResponse",
    "EpisodeActionUploadResponse",
    "PodcastListCreateRequest",
    "PodcastListCreateResponse",
    "PodcastListDocument",
    "PodcastListEntry",
    "PodcastListJsonUpload",
    "PodcastListJsonUploadDocument",
    "PodcastListJsonUploadItem",
    "PodcastListPathRequest",
    "PodcastListQuery",
    "PodcastListRenderPayload",
    "PodcastListRenderResult",
    "PodcastListSummary",
    "PodcastListUpdateRequest",
    "SettingsDocument",
    "SettingsMutationRequest",
    "SettingsScopeQuery",
]
