from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import select

from app.db.models.podcast import EpisodeModel, PodcastFeedModel
from app.services.archive_paths import resolve_archive_path
from app.services.archive_queue import (
    ARCHIVE_STATUS_DONE,
    ARCHIVE_STATUS_DOWNLOADING,
    ARCHIVE_STATUS_ERROR,
    ARCHIVE_STATUS_NONE,
    ARCHIVE_STATUS_QUEUED,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.core.config import Settings


class ArchiveCleanupService:
    def __init__(self, *, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings

    async def disable_archive(self, *, feed_id: int) -> bool:
        feed = (
            await self.session.execute(
                select(PodcastFeedModel).where(PodcastFeedModel.id == feed_id)
            )
        ).scalar_one_or_none()
        if feed is None:
            return False

        feed.archive = False

        active_statuses = (
            ARCHIVE_STATUS_QUEUED,
            ARCHIVE_STATUS_DOWNLOADING,
            ARCHIVE_STATUS_DONE,
            ARCHIVE_STATUS_ERROR,
        )
        episodes = (
            (
                await self.session.execute(
                    select(EpisodeModel).where(
                        EpisodeModel.feed_id == feed_id,
                        EpisodeModel.archive_status.in_(active_statuses),
                    )
                )
            )
            .scalars()
            .all()
        )

        archive_root = Path(self.settings.archive_dir)
        for episode in episodes:
            if episode.archive_status == ARCHIVE_STATUS_DONE and episode.archive_path:
                self._delete_episode_file(archive_root, episode.archive_path)
            episode.archive_status = ARCHIVE_STATUS_NONE
            episode.archive_path = None
            episode.archive_error = None

        await self.session.commit()
        return True

    def _delete_episode_file(self, archive_root: Path, relpath: str) -> None:
        try:
            full = resolve_archive_path(archive_root, relpath)
        except ValueError:
            return
        if full.exists():
            full.unlink(missing_ok=True)
        self._cleanup_empty_parents(archive_root, full.parent)

    def _cleanup_empty_parents(self, archive_root: Path, directory: Path) -> None:
        root = archive_root.resolve()
        current = directory.resolve()
        while current != root and root in current.parents:
            try:
                current.rmdir()
            except OSError:
                break
            current = current.parent
