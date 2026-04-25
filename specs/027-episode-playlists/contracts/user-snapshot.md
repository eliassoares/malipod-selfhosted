# Contracts: User Export/Import (Playlists)

**Feature**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/027-episode-playlists/spec.md`
**Date**: 2026-04-25

Playlists must round-trip through the existing user data tools export/import.

## Snapshot additions

Add two new snapshot arrays:

- `episode_playlists[]`
  - `title`
  - `description` (nullable)
  - `image_url` (nullable)
  - `created_at`
  - `updated_at`

- `episode_playlist_items[]`
  - `playlist_title` (or another stable playlist identifier in snapshot)
  - `episode_url` (or another stable episode identifier)
  - `created_at`

## Notes

- Snapshot should preserve playlist identity in a way that can be re-mapped on import
  without depending on DB ids.
- Favorites is not exported as a playlist (it already exports/imports via `favorite_episodes`).
