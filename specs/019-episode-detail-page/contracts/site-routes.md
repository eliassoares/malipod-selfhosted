# Contracts: Site Routes (Episode Detail Page)

**Feature**: `specs/019-episode-detail-page/spec.md`
**Created**: 2026-04-22

## Route: Episode detail page

**Method**: GET
**Path**: `/episode/{episode_id}`

**Auth**: required (redirect to `/login` when unauthenticated)

**Response**: HTML page with:
- Episode metadata and image (or placeholder).
- Progress display when progress exists for the user.
- Download action when a downloadable URL exists.
- Share action that provides a link to the page.
- Favorite toggle for the episode.
- Optional listening history section (best-effort) when events exist.

## Route: Favorite/unfavorite episode

**Method**: POST
**Path**: `/episode/{episode_id}/favorite`

**Auth**: required
**Idempotency**: duplicates are prevented; toggling is deterministic.

**Response**: redirect back to `/episode/{episode_id}`.

## Route: Download episode

**Method**: GET
**Path**: `/episode/{episode_id}/download`

**Auth**: required
**Behavior**:
- If a downloadable URL exists, respond with a redirect (or streamed file) that
  triggers download behavior in the browser.
- If no downloadable URL exists, respond with a user-friendly redirect back to
  the episode page with an error flag (or hide the action in the UI).
