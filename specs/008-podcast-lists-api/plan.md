# Implementation Plan: Podcast Lists API

**Branch**: `008-podcast-lists-api` | **Date**: 2026-04-16 | **Spec**: [/Users/eliassoares/Documents/projects/personal/malipod/specs/008-podcast-lists-api/spec.md](/Users/eliassoares/Documents/projects/personal/malipod/specs/008-podcast-lists-api/spec.md)
**Input**: Feature specification from `/specs/008-podcast-lists-api/spec.md`

**Note**: This plan delivers the compatibility podcast-lists contracts on top of
the existing FastAPI, SQLAlchemy, and Alembic stack by extending the current
podcast domain with user-owned curated list metadata and ordered feed
membership instead of introducing a separate publishing service.

## Summary

Deliver the Podcast Lists API as an authenticated CRUD surface for curated
podcast collections. The implementation will add list creation with generated
canonical names, public list-summary and list-read endpoints, and authenticated
update/delete flows. The design reuses the current auth flow, podcast feed
entities, and compatibility routing style while introducing a small user-owned
`PodcastList` aggregate plus ordered list items so the service can render the
same stored list in JSON, OPML, or plaintext formats without duplicating feed
metadata.

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
**Performance Goals**: List-summary reads complete in under 300 ms for users
with up to 100 lists, and create/read/update/delete operations on lists with up
to 500 podcast entries complete in under 1 second in a warm local environment
**Constraints**: No new runtime dependencies, list content must support the
same practical formats already used in the podcast-sync domain, canonical names
must be generated deterministically from titles, write endpoints must not allow
cross-account access, and the implementation must not rely on `# noqa`,
`# nosec`, or similar inline suppressions
**Scale/Scope**: Initial podcast-lists compatibility surface only; no website UI
authoring flow, no collaborative editing, no public search or discovery index,
no per-entry annotations beyond feed membership order, and no attempt to enrich
feed metadata beyond what already exists in the podcast domain

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `Spec-First Delivery`: PASS. The feature has a complete spec, this plan, and
  will produce tasks mapped to public reads, authenticated creation, and list
  maintenance slices.
- `Branch Workflow`: PASS. Work is on `008-podcast-lists-api`, created from
  `main`, and will return through the normal pull-request path.
- `Independently Valuable Slices`: PASS. Reading lists, creating lists, and
  updating/deleting lists are independently testable and priority ordered, with
  public reads plus creation forming the MVP foundation.
- `Verification Before Merge`: PASS. The plan defines unit, integration,
  contract, migration, and manual API validation for generated-name behavior,
  summary responses, list rendering, ownership checks, and CRUD flows before
  merge.
- `Strict Python Quality Gates`: PASS. The implementation stays within the
  repository's Python 3.13 toolchain and requires `uv run ruff check .`,
  `uv run mypy app tests`, `uv run bandit -r . -c pyproject.toml`,
  `uv run pip-audit`, and `uv run pytest -q` without suppression shortcuts.
- `Security and Simplicity by Default`: PASS. The design adds no runtime
  dependencies, reuses current auth and podcast-feed patterns, and introduces
  one focused list aggregate plus an ordered join model to satisfy the contract
  without adding new services or background processes.

## Delivery Workflow

- **Base Branch**: `main`
- **Working Branch**: `008-podcast-lists-api` created from `main`
- **Commit Convention**: Conventional Commits required for every commit
- **Merge Policy**: Open a pull request after implementation and verification are complete

## Project Structure

### Documentation (this feature)

```text
specs/008-podcast-lists-api/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── podcast-lists-api.openapi.yaml
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
│   ├── podcast_list.py
│   ├── subscription.py
│   ├── health.py
│   ├── profile.py
│   └── site.py
├── services/
│   ├── auth.py
│   ├── devices.py
│   ├── episodes.py
│   ├── podcast_lists.py
│   ├── subscription_formats.py
│   ├── subscriptions.py
│   ├── localization.py
│   └── readiness.py
└── main.py

alembic/
└── versions/
    └── 0006_podcast_lists.py

tests/
├── contract/
│   ├── test_auth_api.py
│   ├── test_device_api.py
│   ├── test_episodes_api.py
│   ├── test_lists_api.py
│   ├── test_foundation_api.py
│   └── test_subscriptions_api.py
├── integration/
│   ├── test_app_startup.py
│   ├── test_lists_api_flow.py
│   ├── test_profile_page.py
│   ├── test_site_home.py
│   └── test_subscriptions_sync_api.py
└── unit/
    ├── test_episode_service.py
    ├── test_podcast_list_service.py
    ├── test_subscription_formats.py
    └── test_subscription_service.py
```

**Structure Decision**: Keep the existing single `app/` FastAPI project and add
one lists route module, one service module for podcast-list business rules,
matching Pydantic schemas, and one migration that extends the current
podcast-sync domain with list ownership and ordered feed membership. The
existing `podcast.py` model module remains the podcast-domain home for the new
tables so feed, subscription, episode, and list relationships stay co-located.
Tests remain split into unit, integration, and contract suites so generated-name
rules, format rendering, ownership checks, and CRUD compatibility stay isolated
and traceable.

## Phase 0 Research Focus

- Confirm the simplest persistence model for user-owned lists that supports
  deterministic name generation, ordered entries, and multi-format rendering.
- Decide which request and response formats should be reused for list content so
  the feature stays consistent with existing podcast import/export behavior.
- Define the canonical-name normalization rule and fallback behavior when a
  title contains only unsupported characters or collapses to punctuation.
- Choose deterministic ordering for user list summaries and entries within one
  list so read responses remain stable across PostgreSQL and SQLite.

## Phase 1 Design Direction

- Add a `podcast_lists` table keyed by `(user_id, name)` to store ownership,
  human-readable title, canonical name, and timestamps.
- Add an ordered `podcast_list_items` table that joins one list to many
  `podcast_feeds`, preserving entry order and preventing duplicate feed rows
  within the same list.
- Reuse the existing `PodcastFeedModel` as the canonical feed reference,
  creating lightweight placeholder feed rows when list uploads mention feeds not
  yet known locally.
- Reuse the current subscription-format utility pattern for JSON, OPML, and
  plaintext parsing/rendering so create, read, and update logic remain thin and
  the list API contracts stay compatible with the current ecosystem surface.

## Verification Strategy

- Contract tests for:
  - `POST /api/2/lists/{username}/create.{format}`
  - `GET /api/2/lists/{username}.json`
  - `GET /api/2/lists/{username}/list/{listname}.{format}`
  - `PUT /api/2/lists/{username}/list/{listname}.{format}`
  - `DELETE /api/2/lists/{username}/list/{listname}.{format}`
- Unit tests for:
  - canonical-name generation and fallback behavior
  - duplicate-name conflict detection
  - format parsing/rendering for list contents
  - ordered list-item replacement behavior
  - public web URL derivation and stable summary ordering
- Integration tests for:
  - create followed by summary read and list read
  - update followed by format-specific retrieval
  - delete followed by not-found verification
  - cross-account access denial and missing-resource behavior
- Repository quality gates:
  - `uv run ruff check .`
  - `uv run mypy app tests`
  - `uv run bandit -r . -c pyproject.toml`
  - `uv run pip-audit`
  - `uv run pytest -q`
- Manual validation:
  - curl-driven list creation returning `303 See Other`
  - summary read for one user in JSON
  - individual list reads in JSON, OPML, and plaintext
  - update and delete flows for owned lists plus one cross-account denial case

## Complexity Tracking

No constitution violations identified for this plan.
