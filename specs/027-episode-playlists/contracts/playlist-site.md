# Contracts: Episode Playlists (Site)

**Feature**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/027-episode-playlists/spec.md`
**Date**: 2026-04-25

This feature is site-only (server-rendered UI). No gpodder protocol endpoints are
changed.

## Pages

### Manage playlists

`GET /user/{nickname}/playlists`

- **Auth**: required
- **Owner-only**: nickname must match current user.
- Lists:
  - User playlists (editable/deletable)
  - Virtual “Favorites” playlist (read-only)
- Includes a “Create playlist” action that opens a modal (name/description/image).

### Playlist detail

`GET /user/{nickname}/playlists/{playlist_id}`

- **Auth**: required
- **Owner-only**: playlist must belong to current user.
- Shows:
  - playlist metadata + metrics (episode count, created_at, listened/total time, image/placeholder)
  - list of episodes in the playlist
  - search box to find episodes and add/remove them from playlist

## Actions (Forms)

### Create playlist

`POST /user/{nickname}/playlists/create`

Form fields:
- `title` (required)
- `description` (optional, <= 1024 chars)
- `image` (optional upload, <= 1MB)

### Update playlist

`POST /user/{nickname}/playlists/{playlist_id}/update`

Same fields/validation as create.

### Delete playlist

`POST /user/{nickname}/playlists/{playlist_id}/delete`

- Requires explicit confirmation in the UI modal.
- Must not apply to Favorites.

### Add/remove episodes in playlist

`POST /user/{nickname}/playlists/{playlist_id}/items`

Form fields:
- `episode_id` (required)
- `action`: `add` or `remove`

### Add episode to multiple playlists (episode detail popup)

`POST /user/{nickname}/episode/{episode_id}/playlists`

Form fields:
- `playlist_ids`: list of playlist ids to add membership to.

Constraints:
- No duplicates per `(playlist_id, episode_id)`.
- Owner-only: playlists must belong to current user.
