# Data Model: Episode Playlists

**Feature**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/027-episode-playlists/spec.md`
**Date**: 2026-04-25

## New Entities (Persistence)

### EpisodePlaylist

Represents a user-owned playlist of episodes.

- Owner: user
- Fields:
  - `id`
  - `user_id`
  - `title` (required)
  - `description` (optional, max 1024 chars)
  - `image_url` (optional; if empty, UI uses placeholder)
  - `created_at`, `updated_at`

Constraints:
- Playlist titles are user-scoped; name/slug can be derived for URLs if needed.
- Only the owner can read/write.

### EpisodePlaylistItem

Connects episodes to a playlist.

- Fields:
  - `id`
  - `playlist_id`
  - `episode_id`
  - `created_at`

Constraints:
- Unique `(playlist_id, episode_id)` to prevent duplicates.
- Deletes cascade when playlist is deleted.

## Existing Entities Used

- **Episode**: the canonical episode record being referenced by playlists.
- **FavoriteEpisode**: powers the “Favorites” virtual playlist.
- **EpisodeActionEvent / EpisodeAction**: used to compute listened and total time metrics.
- **PodcastFeed**: displayed alongside episode information where relevant.

## Derived Views (No New Tables)

- **Favorites playlist**: virtual playlist derived from favorite episodes.
- **Playlist metrics**:
  - Episode count: `count(items)`
  - Listened seconds: sum of best-known play positions for episodes in the playlist
  - Total seconds: sum of best-known totals for episodes in the playlist (when available)

## Data Validation

- Description max length: 1024 characters (reject on create/update).
- Image upload size: max 1MB (reject on create/update if exceeded).
