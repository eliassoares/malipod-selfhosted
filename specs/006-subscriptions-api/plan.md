# Implementation Plan: Subscriptions API

**Branch**: `006-subscriptions-api` | **Date**: 2026-04-16 | **Spec**: [/Users/eliassoares/Documents/projects/personal/malipod/specs/006-subscriptions-api/spec.md](/Users/eliassoares/Documents/projects/personal/malipod/specs/006-subscriptions-api/spec.md)
**Input**: Feature specification from `/specs/006-subscriptions-api/spec.md`

**Note**: This plan delivers the compatibility subscriptions contracts on top of
the existing FastAPI, SQLAlchemy, and Alembic stack by extending the already
introduced device and podcast-sync domain instead of creating a separate sync
service.

## Summary

Deliver the Subscriptions API as an authenticated extension of the current
device-sync feature set. The implementation will add account-wide and
per-device subscription reads in OPML, JSON, and plaintext formats, full-device
subscription replacement with automatic device creation, and incremental
add/remove synchronization backed by a server-issued change-history record. The
design reuses the current auth flow, device ownership checks, podcast feed
models, and `/api/2` compatibility style while keeping format parsing/rendering
and delta bookkeeping inside the existing application.

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
**Performance Goals**: Device/account subscription reads complete in under 500
ms for normal local usage, and delta upload/read complete in under 1 second for
devices with up to 1,000 recorded subscription changes in a warm local
environment
**Constraints**: No new runtime dependencies, format support is limited to OPML,
JSON, plaintext, and JSONP only where the response shape supports it, device and
ownership boundaries must not leak cross-account data, successful full uploads
must return an empty body, and the implementation must not rely on `# noqa`,
`# nosec`, or other inline quality suppressions
**Scale/Scope**: Initial subscriptions compatibility surface only; no web UI for
subscription management, no background feed refresh, no cross-device merge UI,
and no episode-state sync changes beyond keeping the podcast/feed domain
consistent

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `Spec-First Delivery`: PASS. The feature already has a concrete spec, this
  plan, and will produce tasks mapped to read, full-upload, and delta-sync
  slices.
- `Branch Workflow`: PASS. Work remains on `006-subscriptions-api`, created from
  `main`, and will return through the normal pull-request path.
- `Independently Valuable Slices`: PASS. Device/account reads, full-device
  replacement, and incremental deltas are independently testable and ordered so
  the read/bootstrap path ships before delta synchronization.
- `Verification Before Merge`: PASS. The plan requires unit, integration,
  contract, migration, and manual API validation for formats, empty-body upload
  success, auto-created devices, URL sanitation, conflict rejection, and
  timestamp filtering before merge.
- `Strict Python Quality Gates`: PASS. The implementation stays within the
  existing Python 3.13 toolchain and requires `uv run ruff check .`,
  `uv run mypy app tests`, `uv run bandit -r . -c pyproject.toml`,
  `uv run pip-audit`, and `uv run pytest -q` without suppression shortcuts.
- `Security and Simplicity by Default`: PASS. The design adds no new runtime
  dependency, reuses existing auth and DB patterns, and introduces only one
  focused change-history persistence addition to support server-issued sync
  timestamps.

## Delivery Workflow

- **Base Branch**: `main`
- **Working Branch**: `006-subscriptions-api` created from `main`
- **Commit Convention**: Conventional Commits required for every commit
- **Merge Policy**: Open a pull request after implementation and verification are complete

## Project Structure

### Documentation (this feature)

```text
specs/006-subscriptions-api/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── subscriptions-api.openapi.yaml
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
│   ├── subscription.py
│   ├── health.py
│   ├── profile.py
│   └── site.py
├── services/
│   ├── auth.py
│   ├── devices.py
│   ├── subscription_formats.py
│   ├── subscriptions.py
│   ├── localization.py
│   └── readiness.py
└── main.py

alembic/
└── versions/
    └── 0004_subscription_sync_history.py

tests/
├── contract/
│   ├── test_auth_api.py
│   ├── test_device_api.py
│   └── test_subscriptions_api.py
├── integration/
│   ├── test_device_updates_api.py
│   └── test_subscriptions_sync_api.py
└── unit/
    ├── test_device_service.py
    ├── test_subscription_formats.py
    └── test_subscription_service.py
```

**Structure Decision**: Keep the existing single `app/` FastAPI project and add
one subscriptions route module, one service module for business rules, one small
format utility module for parsing/rendering OPML/JSON/plaintext, matching
Pydantic schemas, and one migration that extends the current podcast-sync
entities with change-history persistence. Tests remain split into unit,
integration, and contract suites so parsing, ownership, replacement semantics,
and delta compatibility are all isolated and traceable.

## Phase 0 Research Focus

- Confirm the simplest way to represent server-issued timestamps for delta sync
  without introducing a separate event store service.
- Decide how JSONP should be applied only to compatible JSON read responses
  without affecting upload or delta endpoints.
- Define deterministic ordering rules for account-wide and device-specific
  subscription exports across multiple persisted rows.
- Choose lightweight OPML parsing/rendering that stays inside the standard
  library and existing dependency set.

## Phase 1 Design Direction

- Extend the podcast-sync data model with a subscription change-history table
  keyed by an auto-incrementing integer that doubles as the API timestamp.
- Reuse `devices` plus `device_subscriptions` for active-state storage, and emit
  change records for both full replacement and delta upload so later reads using
  `since` remain coherent.
- Centralize format parsing and serialization in dedicated utilities to keep the
  API route thin and make contract tests format-focused rather than route-heavy.
- Keep authentication and ownership enforcement aligned with the existing device
  API helper flow to prevent cross-account leakage.

## Verification Strategy

- Contract tests for:
  - `GET /subscriptions/{username}/{deviceid}.{format}`
  - `GET /subscriptions/{username}.{format}`
  - `PUT /subscriptions/{username}/{deviceid}.{format}`
  - `POST /api/2/subscriptions/{username}/{deviceid}.json`
  - `GET /api/2/subscriptions/{username}/{deviceid}.json`
- Unit tests for:
  - format parsing/rendering and JSONP wrapping rules
  - URL sanitation and duplicate normalization
  - delta conflict detection and timestamp filtering
  - full replacement diff generation and device auto-creation behavior
- Integration tests for:
  - account-wide union reads across multiple devices
  - full upload followed by delta read using returned timestamps
  - invalid device/account access behavior and empty-body success responses
- Repository quality gates:
  - `uv run ruff check .`
  - `uv run mypy app tests`
  - `uv run bandit -r . -c pyproject.toml`
  - `uv run pip-audit`
  - `uv run pytest -q`
- Manual validation:
  - curl-driven verification for all supported formats
  - auto-created device on first full upload
  - `update_urls` behavior for sanitized invalid URLs
  - unchanged delta-read response returning empty `add`/`remove` plus fresh timestamp

## Complexity Tracking

No constitution violations identified for this plan.
