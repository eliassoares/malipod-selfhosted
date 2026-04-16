# Implementation Plan: Episodes API

**Branch**: `007-episodes-api` | **Date**: 2026-04-16 | **Spec**: [/Users/eliassoares/Documents/projects/personal/malipod/specs/007-episodes-api/spec.md](/Users/eliassoares/Documents/projects/personal/malipod/specs/007-episodes-api/spec.md)
**Input**: Feature specification from `/specs/007-episodes-api/spec.md`

**Note**: This plan adds the compatibility episode-actions surface by extending
the existing podcast-sync domain with user-scoped episode action uploads,
append-only action history, filtered retrieval, and aggregated latest-state
reads while preserving the current device-update behavior already built on top
of the same episode/feed entities.

## Summary

Deliver the Episodes API as an authenticated extension of the current sync
surface. The implementation will add `POST /api/2/episodes/{username}.json` and
`GET /api/2/episodes/{username}.json`, support the documented action types,
sanitize podcast and episode URLs, and provide server-issued timestamps for
incremental retrieval. The design reuses the existing auth flow, podcast feed
and episode entities, and device-ID validation rules, but introduces a separate
append-only episode-action history so clients can retrieve all matching events
since a prior sync point without breaking the repository's current
latest-state-per-episode projection.

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: FastAPI, Starlette, Pydantic Settings, SQLAlchemy 2.x,
Alembic, asyncpg, aiosqlite, httpx, pytest, pytest-asyncio
**Storage**: PostgreSQL for runtime and development, SQLite for automated tests
**Testing**: pytest, FastAPI TestClient/httpx, Ruff, MyPy, Bandit, pip-audit
**Target Platform**: Authenticated compatibility API served by the existing
FastAPI application in local Docker Compose and test environments
**Project Type**: Single FastAPI web application with ORM-backed persistence and
contract-focused API routes
**Performance Goals**: Episode-action upload requests complete in under 500 ms
for normal batches of up to 100 actions, and filtered retrieval requests
complete in under 1 second for users with up to 10,000 stored action events in
a warm local environment
**Constraints**: No new runtime dependencies, upload and retrieval behavior must
remain compatible with the documented `/api/2/episodes` contracts, invalid or
rewritten URLs must be ignored semantically and reported through `update_urls`,
cross-account requests must not leak user history, and the implementation must
not rely on `# noqa`, `# nosec`, or similar inline suppressions
**Scale/Scope**: Initial episode-actions compatibility surface only; no website
UI for browsing action logs, no background retention or compaction jobs, no new
action types beyond the documented set, and no attempt to redesign the existing
device updates endpoint beyond keeping it compatible with the new history model

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `Spec-First Delivery`: PASS. The feature has a complete spec, this plan, and
  will produce a traceable task breakdown mapped to upload, retrieval, and
  filter/aggregation slices.
- `Branch Workflow`: PASS. Work is on `007-episodes-api`, created from `main`,
  and will return through the normal pull-request path.
- `Independently Valuable Slices`: PASS. Upload, retrieval, and filtered or
  aggregated retrieval remain independently testable and priority ordered, with
  upload and basic retrieval forming the MVP foundation.
- `Verification Before Merge`: PASS. The plan defines unit, integration,
  contract, migration, and manual API validation for action upload, `play`
  validation, URL sanitation, incremental retrieval, filters, and aggregation
  before merge.
- `Strict Python Quality Gates`: PASS. The implementation stays within the
  repository's Python 3.13 toolchain and requires `uv run ruff check .`,
  `uv run mypy app tests`, `uv run bandit -r . -c pyproject.toml`,
  `uv run pip-audit`, and `uv run pytest -q` without suppression shortcuts.
- `Security and Simplicity by Default`: PASS. The design adds no runtime
  dependencies, reuses current auth and sync-domain entities, and introduces one
  focused append-only history model plus a lightweight latest-state projection
  update path to satisfy retrieval and aggregation needs.

## Delivery Workflow

- **Base Branch**: `main`
- **Working Branch**: `007-episodes-api` created from `main`
- **Commit Convention**: Conventional Commits required for every commit
- **Merge Policy**: Open a pull request after implementation and verification are complete

## Project Structure

### Documentation (this feature)

```text
specs/007-episodes-api/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── episodes-api.openapi.yaml
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
│   ├── subscription.py
│   ├── health.py
│   ├── profile.py
│   └── site.py
├── services/
│   ├── auth.py
│   ├── devices.py
│   ├── episodes.py
│   ├── localization.py
│   ├── readiness.py
│   └── subscriptions.py
└── main.py

alembic/
└── versions/
    └── 0005_episode_action_history.py

tests/
├── contract/
│   ├── test_auth_api.py
│   ├── test_device_api.py
│   ├── test_episodes_api.py
│   └── test_subscriptions_api.py
├── integration/
│   ├── test_device_updates_api.py
│   ├── test_episodes_sync_api.py
│   └── test_subscriptions_sync_api.py
└── unit/
    ├── test_device_service.py
│   ├── test_episode_service.py
│   ├── test_subscription_formats.py
│   └── test_subscription_service.py
```

**Structure Decision**: Keep the existing single `app/` FastAPI project and add
one episodes route module, one service module for episode-action business rules,
matching Pydantic schemas, and one migration that extends the sync domain with
append-only episode-action history. The current `EpisodeActionModel` remains the
latest-state projection used by device updates, while the new history entity
supplies sync timestamps and full retrieval semantics. Tests remain split into
unit, integration, and contract suites so validation rules, filtering behavior,
aggregation, and API compatibility stay independently traceable.

## Phase 0 Research Focus

- Confirm the simplest way to preserve full upload history while still exposing
  the latest episode action for existing device-update behavior.
- Decide how `aggregated=true` should be derived from the stored history without
  losing deterministic ordering.
- Define safe URL sanitation for episodes that extends the current subscription
  sanitizer to reject non-ASCII URLs as required by the spec.
- Clarify how optional device IDs should interact with filtering when the device
  was never explicitly registered.

## Phase 1 Design Direction

- Add an append-only `episode_action_events` table with an auto-incrementing ID
  that doubles as the API timestamp for uploads and retrieval.
- Keep `EpisodeActionModel` as the per-user latest-state projection, updating it
  whenever a new valid action event is appended so existing sync flows stay
  compatible.
- Reuse existing `podcast_feeds` and `episodes` entities, creating minimal
  placeholder feed or episode records when uploads reference URLs not yet known
  locally.
- Centralize upload validation, URL sanitation, aggregation, and filtering in a
  dedicated episodes service so the route remains thin and contract-focused.

## Verification Strategy

- Contract tests for:
  - `POST /api/2/episodes/{username}.json`
  - `GET /api/2/episodes/{username}.json`
- Unit tests for:
  - action-type and `play`-field validation
  - URL sanitation and `update_urls` generation
  - timestamp issuance and `since` filtering
  - podcast/device filtering and aggregated latest-action reads
  - latest-state projection updates for existing episode-sync behavior
- Integration tests for:
  - multi-action upload batches
  - retrieval with and without `since`
  - empty retrieval responses
  - filtering by podcast and device
  - aggregation returning only the latest action per episode
- Repository quality gates:
  - `uv run ruff check .`
  - `uv run mypy app tests`
  - `uv run bandit -r . -c pyproject.toml`
  - `uv run pip-audit`
  - `uv run pytest -q`
- Manual validation:
  - curl-driven upload and retrieval of mixed action batches
  - `play` validation failures for incomplete progress fields
  - `update_urls` output for sanitized podcast and episode URLs
  - retrieval using `since`, `podcast`, `device`, and `aggregated=true`

## Complexity Tracking

No constitution violations identified for this plan.
