# Favorites API PR Summary

## Implemented Scope

- Added authenticated compatibility endpoint:
  - `GET /api/2/favorites/{username}.json`
- Introduced `favorite_episodes` persistence to track one user's favorites
  without duplicating podcast or episode metadata
- Reused existing `PodcastFeedModel` and `EpisodeModel` data to serialize:
  - `title`
  - `url`
  - `podcast_title`
  - `podcast_url`
  - `description`
  - `website`
  - `released`
  - `mygpo_link`
- Enforced stable ordering by `favorited_at DESC, episode_id ASC`
- Added authentication, cross-account protection, and missing-user handling
- Added contract, integration, unit, and startup registration coverage for the
  new favorites route

## Verification

- `uv run ruff check .`
- `uv run mypy app tests`
- `uv run bandit -r . -c pyproject.toml`
- `uv run pip-audit`
- `uv run pytest -q`
- `uv run pytest -q tests/unit/test_favorite_service.py tests/contract/test_favorites_api.py tests/integration/test_favorites_api_flow.py tests/integration/test_app_startup.py`
- Manual-guided validation via `TestClient` confirmed:
  - populated favorites response returns `200 OK`
  - empty favorites response returns `200 OK` with `[]`
  - unauthenticated request returns `401 Unauthorized`
  - cross-account request returns `403 Forbidden`
  - missing username returns `404 Not Found`

## Migration Notes

- Added Alembic revision `0008_favorite_episodes`
- Introduced new table:
  - `favorite_episodes`

## Follow-ups

- If the product later exposes favorite creation or removal through the API,
  those endpoints can build on the same projection table without changing the
  read contract implemented here.

---

# Device Sync API PR Summary

## Implemented Scope

- Added authenticated compatibility endpoint:
  - `GET /api/2/sync-devices/{username}.json`
  - `POST /api/2/sync-devices/{username}.json`
- Implemented deterministic status output:
  - `synchronized`: list of 2+ device IDs per group (sorted)
  - `not-synchronized`: list of device IDs not in any group (sorted)
- Implemented idempotent group mutations:
  - merge groups via `synchronize`
  - remove devices via `stop-synchronize`
  - cleanup groups with fewer than 2 members
- Enforced ownership via existing `authenticate_api_user`
- Added contract, integration, and unit coverage for GET/POST behavior, access
  control, idempotency, and atomic no-partial-apply semantics

## Verification

- `uv run ruff check .`
- `uv run mypy app tests`
- `uv run bandit -r . -c pyproject.toml`
- `uv run pip-audit`
- `uv run pytest -q`

## Migration Notes

- Added Alembic revision `0009_device_sync_groups`
- Introduced new table:
  - `device_sync_groups`
- Added new column:
  - `devices.sync_group_id`

## Follow-ups

- If future compatibility endpoints need to resolve a “current device group”
  beyond membership (e.g., group metadata), we can extend `device_sync_groups`
  without changing the current contract.

---

# Client Parametrization PR Summary

## Implemented Scope

- Added public client auto-configuration endpoint:
  - `GET /clientconfig.json`
- Returns JSON with:
  - `mygpo.baseurl` (normalized with trailing slash)
  - `mygpo-feedservice.baseurl` (compatibility; same value)
  - `update_timeout` (positive integer; fixed default 86400 seconds)
- Endpoint is stateless and does not perform any DB writes.

## Verification

- `make check`
- `make test`
- Contract coverage added for `/clientconfig.json`:
  - `uv run pytest -q tests/contract/test_client_config.py`

---

# Directory API PR Summary

## Implemented Scope

- Added public Directory API endpoints backed only by local subscription catalog:
  - `GET /search.{json|opml|txt}?q=...`
  - `GET /toplist/{number}.{json|opml|txt}`
  - `GET /api/2/tags/{count}.json`
  - `GET /api/2/tag/{tag}/{count}.json`
  - `GET /api/2/data/podcast.json?url=...`
  - `GET /api/2/data/episode.json?podcast=...&url=...`
- Enforced `count`/`number` bounds (1–100) with `400 Bad Request` on out-of-range.
- Computed `subscribers` as distinct users with active subscriptions per feed.
- Built `mygpo_link` using the server `base_url` (no gpodder.net hardcoding).
- Added optional feed metadata fields to support tags and richer podcast data:
  - `podcast_feeds.author`
  - `podcast_feeds.categories` (JSON list)

## Verification

- `make check`
- `make test`
- Contract coverage added for Directory API:
  - `uv run pytest -q tests/contract/test_directory_api.py`

---

# Podcast Detail Page PR Summary

## Implemented Scope

- Added authenticated podcast detail page:
  - `GET /podcast/{podcast_id}`
  - Renders podcast metadata (title, description, website, author, categories, image/placeholder)
  - Renders complete episode list with per-episode placeholder images
  - Supports sorting episodes by date (`sort=recent|oldest`) with a mobile-friendly selector
- Added site actions from the podcast detail page:
  - `POST /podcast/{podcast_id}/subscribe` (idempotent; schedules feed import outside tests)
  - `POST /podcast/{podcast_id}/favorite` (toggle)
- Added favorites persistence for podcasts:
  - New table `favorite_podcasts` (unique per `user_id` + `feed_id`)
  - New service `PodcastFavoritesService` for querying/toggling favorites
- Extended subscriptions page with a favorites-only filter:
  - Toggle UI + query param `favorites=1`
  - Empty state messaging when no favorites exist
- Improved feed import metadata ingestion (best-effort):
  - Captures `author` and `categories` from RSS/Atom when present
  - Captures per-episode logo URL when present

## Verification

- `uv run pytest` (285 passed)
- `uv run ruff check .`
- `uv run mypy .`
- `uv run bandit -r app -c pyproject.toml`

## Migration Notes

- Added Alembic revision `0013_favorite_podcasts`
- Introduced new table:
  - `favorite_podcasts`

## Follow-ups

- If desired, we can persist the subscriptions favorites filter preference per user (currently query-param based).

---

# Episode Detail Page PR Summary

## Implemented Scope

- Added authenticated episode detail page:
  - `GET /episode/{episode_id}`
  - Renders episode metadata (title, description, release date, podcast title, image/placeholder)
  - Renders user progress when present (watched/total + progress bar)
- Added episode actions:
  - `GET /episode/{episode_id}/download` (redirects to `media_url` when present)
  - `POST /episode/{episode_id}/favorite` (toggle)
  - Share button that exposes the canonical episode URL (`{base_url}/episode/{id}`)
- Added listening history section (best-effort) using recent action events with an empty state.
- Linked podcast episode list items to the episode detail page.
- Added integration coverage for episode detail page behavior (rendering, 404, progress, download, share, favorite, history).

## Verification

- `uv run pytest` (296 passed)
- `uv run ruff check .`
- `uv run mypy .`
- `uv run bandit -r app -c pyproject.toml`

## Migration Notes

- Added Alembic revision `0014_episode_media_url`
- Added new column:
  - `episodes.media_url`

## Follow-ups

- Optional: replace clipboard-only share UX with a fallback (e.g., readonly input) for browsers that block `navigator.clipboard`.
