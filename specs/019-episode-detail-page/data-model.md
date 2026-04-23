# Data Model: Episode Detail Page

**Feature**: `specs/019-episode-detail-page/spec.md`
**Created**: 2026-04-22

## Existing Entities (relevant)

### Episode (`episodes`)

Represents a podcast episode with metadata.

Key fields (existing):
- `id` (primary key)
- `feed_id` (FK to `podcast_feeds.id`)
- `episode_url` (unique)
- `title`, `description`, `website`, `logo_url`, `released_at`

### Favorite Episode (`favorite_episodes`)

Represents a per-user favorite marker for an episode.

Key fields (existing):
- `user_id`, `episode_id` (unique pair)
- `favorited_at`

### Episode Action / Progress (`episode_actions`)

Represents per-user per-episode projection of the latest action (used for
progress display).

Key fields (existing):
- `user_id`, `episode_id` (unique pair)
- `status` (e.g., play/new/…)
- `action` (JSON payload that may contain `position`, `total`, etc.)
- `occurred_at`

### Episode Action Events (`episode_action_events`)

Represents per-user event history for episodes (best-effort “listening history”
source for the detail page).

Key fields (existing):
- `user_id`, `episode_id`
- `action` + `occurred_at`

## Derived Views (query intent)

- **Episode detail**: fetch episode by `id`, determine favorite existence, fetch
  latest action/progress projection, optionally list recent action events for
  history.
