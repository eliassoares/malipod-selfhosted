# Contracts: Site Routes (Podcast Detail Page)

**Feature**: `specs/018-podcast-detail-page/spec.md`
**Created**: 2026-04-22

## Route: Podcast detail page

**Method**: GET
**Path**: `/podcast/{podcast_id}`

**Auth**: required (redirect to `/login` when unauthenticated)

**Query parameters**:
- `sort`: `recent` (default) or `oldest`

**Response**: HTML page with:
- Podcast metadata: title, description, website (when present), author (when present), categories (when present), image.
- Episode list: all episodes, ordered per `sort`.
- Actions:
  - Subscribe (shown when the user is not subscribed).
  - Favorite toggle (shown always for authenticated users).

## Route: Subscribe to podcast (from detail page)

**Method**: POST
**Path**: `/podcast/{podcast_id}/subscribe`

**Auth**: required
**Idempotency**: repeated calls do not create duplicate subscriptions

**Response**: redirect back to `/podcast/{podcast_id}` with a success/error flag.

## Route: Favorite/unfavorite podcast (from detail page)

**Method**: POST
**Path**: `/podcast/{podcast_id}/favorite`

**Auth**: required
**Idempotency**: toggling is deterministic; creating duplicates is prevented by the unique constraint.

**Response**: redirect back to `/podcast/{podcast_id}` with the updated state.

## Route: Subscriptions page favorites-only filter

**Method**: GET
**Path**: `/user/subscriptions/{nickname}`

**Query parameters**:
- `favorites`: `1` to filter to favorites only (default: absent/0)
- Existing parameters remain supported: `q`, `sort`, `view`

**Response**: HTML page listing subscriptions, filtered when `favorites=1`.
