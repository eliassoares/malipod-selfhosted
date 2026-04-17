# Implementation Plan: Favorites API

**Branch**: `010-favorites-api` | **Date**: 2026-04-17 | **Spec**: [/Users/eliassoares/Documents/projects/personal/malipod/specs/010-favorites-api/spec.md](/Users/eliassoares/Documents/projects/personal/malipod/specs/010-favorites-api/spec.md)
**Input**: Feature specification from `/specs/010-favorites-api/spec.md`

**Note**: This plan delivers the gpodder-compatible favorites endpoint on top of
the existing FastAPI, SQLAlchemy, and Alembic stack by adding one authenticated
read-only API surface plus a focused user-to-episode favorites projection that
reuses the current podcast and episode metadata already present in the sync
domain.

## Summary

Deliver the Favorites API as an authenticated read-only compatibility surface
for favorite episodes. The implementation will add
`GET /api/2/favorites/{username}.json`, enforce account ownership through the
existing HTTP Basic pattern, and return favorite episode items enriched with
episode and podcast metadata. The design reuses the current auth flow,
`PodcastFeedModel`, and `EpisodeModel`, while introducing a small
`FavoriteEpisode` projection keyed by `(user_id, episode_id)` so favorites can
be queried and ordered without coupling the endpoint to unfinished settings or
website-only behavior.

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: FastAPI, Starlette, Pydantic Settings, SQLAlchemy 2.x, Alembic, asyncpg, aiosqlite, httpx, pytest, pytest-asyncio
**Storage**: PostgreSQL for runtime and development, SQLite for automated tests
**Testing**: pytest, FastAPI TestClient/httpx, Ruff, MyPy, Bandit, pip-audit
**Target Platform**: Authenticated compatibility API served by the existing FastAPI application in local Docker Compose and test environments
**Project Type**: Single FastAPI web application with ORM-backed persistence and contract-focused API routes
**Performance Goals**: Favorites reads should complete in under 300 ms for a warm local request and users with up to 1,000 favorite episodes should receive a stable JSON payload in under 1 second locally
**Constraints**: No new runtime dependencies, the endpoint requires authentication, cross-account reads must be denied, response ordering must remain stable across PostgreSQL and SQLite, the implementation must preserve documented response fields, and the solution must not rely on `# noqa`, `# nosec`, or similar inline suppressions
**Scale/Scope**: Initial favorites compatibility surface only; supports read-only retrieval for one authenticated user, no favorite mutation endpoint in this feature, no public favorites feed, no recommendation logic, and no expansion into website UI or social features

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `Spec-First Delivery`: PASS. The feature has a completed spec, this plan, and
  will produce a traceable task breakdown mapped to favorite retrieval,
  metadata serialization, and access-control slices.
- `Branch Workflow`: PASS. Work is on `010-favorites-api`, created from `main`,
  and will return through the normal pull-request path.
- `Independently Valuable Slices`: PASS. Reading favorites, preserving favorite
  metadata, and enforcing favorites access controls are independently testable
  and priority ordered, with favorite retrieval forming the MVP.
- `Verification Before Merge`: PASS. The plan defines unit, contract,
  integration, migration, and manual API validation for successful favorite
  retrieval, empty responses, metadata mapping, cross-account denial, and
  missing-user behavior before merge.
- `Strict Python Quality Gates`: PASS. The implementation stays within the
  repository's Python 3.13 toolchain and requires `uv run ruff check .`,
  `uv run mypy app tests`, `uv run bandit -r . -c pyproject.toml`,
  `uv run pip-audit`, and `uv run pytest -q` without suppression shortcuts.
- `Security and Simplicity by Default`: PASS. The design adds no runtime
  dependencies, reuses current auth and episode/feed metadata, and introduces
  one small favorites projection instead of coupling this read-only endpoint to
  unfinished settings behavior or broader recommendation systems.

## Delivery Workflow

- **Base Branch**: `main`
- **Working Branch**: `010-favorites-api` created from `main`
- **Commit Convention**: Conventional Commits required for every commit
- **Merge Policy**: Open a pull request after implementation and verification are complete

## Project Structure

### Documentation (this feature)

```text
specs/010-favorites-api/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── favorites-api.openapi.yaml
└── tasks.md
```

### Source Code (repository root)

```text
app/
├── api/
│   ├── deps.py
│   └── routes/
│       ├── auth_api.py
│       ├── devices_api.py
│       ├── episodes_api.py
│       ├── favorites_api.py
│       ├── lists_api.py
│       ├── subscriptions_api.py
│       ├── health.py
│       ├── profile_site.py
│       └── site.py
├── core/
│   ├── config.py
│   ├── localization.py
│   ├── logging.py
│   └── security.py
├── db/
│   ├── base.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── device.py
│   │   ├── foundation.py
│   │   ├── podcast.py
│   │   ├── session.py
│   │   └── user.py
│   └── session.py
├── schemas/
│   ├── auth.py
│   ├── device.py
│   ├── episode.py
│   ├── favorite.py
│   ├── health.py
│   ├── podcast_list.py
│   ├── profile.py
│   ├── site.py
│   └── subscription.py
├── services/
│   ├── auth.py
│   ├── devices.py
│   ├── episodes.py
│   ├── favorites.py
│   ├── podcast_lists.py
│   ├── readiness.py
│   ├── subscription_formats.py
│   └── subscriptions.py
└── main.py

alembic/
└── versions/
    └── 0008_favorite_episodes.py

tests/
├── contract/
│   ├── test_auth_api.py
│   ├── test_device_api.py
│   ├── test_episodes_api.py
│   ├── test_favorites_api.py
│   ├── test_foundation_api.py
│   ├── test_lists_api.py
│   └── test_subscriptions_api.py
├── integration/
│   ├── test_app_startup.py
│   ├── test_episodes_sync_api.py
│   ├── test_favorites_api_flow.py
│   ├── test_lists_api_flow.py
│   ├── test_site_home.py
│   └── test_subscriptions_sync_api.py
└── unit/
    ├── test_episode_service.py
    ├── test_favorite_service.py
    ├── test_podcast_list_service.py
    ├── test_subscription_formats.py
    └── test_subscription_service.py
```

**Structure Decision**: Keep the existing single `app/` FastAPI project and add
one favorites route module, one service module for favorite-episode retrieval,
matching Pydantic schemas, and one migration that adds a focused user-to-episode
favorites projection. The new favorites projection will live in the existing
podcast-domain model module so it stays close to `EpisodeModel` and
`PodcastFeedModel`, keeping episode metadata and favorite ownership in one
place. Tests remain split into unit, integration, and contract suites so
ordering, metadata serialization, and ownership behavior remain traceable.

## Phase 0 Research Focus

- Confirm the simplest persistence model for favorite episodes that supports
  read-only retrieval, stable ordering, and no duplicate episode rows per user.
- Decide how favorite items should source podcast and episode metadata from the
  existing episode/feed domain rather than copying large payloads into a new
  favorites table.
- Define stable favorites ordering that works predictably across PostgreSQL and
  SQLite and remains compatible with repeated client syncs.
- Clarify how missing optional metadata fields should appear in the response so
  favorite items remain serializable even when some episode or feed attributes
  are absent.

## Phase 1 Design Direction

- Add a `favorite_episodes` table keyed by `(user_id, episode_id)` with a
  `favorited_at` timestamp used for deterministic ordering.
- Reuse `EpisodeModel` and `PodcastFeedModel` as the canonical metadata source
  for response items so the favorites endpoint exposes current episode and
  podcast details without storing redundant copies.
- Implement one `FavoritesService` that loads favorite episode rows, joins the
  related episode and feed records, deduplicates by relational constraints, and
  serializes the documented response fields.
- Add one `favorites_api.py` router under `/api/2` that follows the current
  HTTP Basic ownership pattern from episodes and subscriptions and maps missing
  users or unauthorized access to compatibility HTTP responses.

## Verification Strategy

- Contract tests for:
  - `GET /api/2/favorites/{username}.json`
- Unit tests for:
  - favorite-item serialization from episode and podcast metadata
  - stable favorites ordering
  - duplicate favorite prevention through the projection model
  - empty favorite list handling
- Integration tests for:
  - successful retrieval of one or more favorites
  - empty favorite response for a valid user
  - cross-account denial
  - missing-user not-found behavior
  - metadata fields with optional null or empty values
- Repository quality gates:
  - `uv run ruff check .`
  - `uv run mypy app tests`
  - `uv run bandit -r . -c pyproject.toml`
  - `uv run pip-audit`
  - `uv run pytest -q`
- Manual validation:
  - curl-driven authenticated favorites read
  - one response with populated metadata
  - one response with no favorites
  - one cross-account denial case
  - one missing-user case

## Complexity Tracking

No constitution violations identified for this plan.
