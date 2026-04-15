# Implementation Plan: Device API

**Branch**: `005-device-api` | **Date**: 2026-04-15 | **Spec**: [/Users/eliassoares/Documents/projects/personal/malipod/specs/005-device-api/spec.md](/Users/eliassoares/Documents/projects/personal/malipod/specs/005-device-api/spec.md)
**Input**: Feature specification from `/specs/005-device-api/spec.md`

**Note**: This plan adds the first device-management and device-sync API
capabilities to Malipod by extending the current FastAPI application with
device registration, device listing, and incremental device update retrieval
while reusing the existing authentication, database, and contract-testing
infrastructure.

## Summary

Deliver the Device API as a focused extension of the existing authenticated JSON
surface. The implementation will add persistent device records scoped per user,
minimal sync-domain tables needed to express subscriptions and episode update
history, and a small service layer that enforces ownership, device-ID
validation, partial updates, and timestamp-based incremental retrieval. The plan
intentionally stays inside the current FastAPI, SQLAlchemy, Alembic, and pytest
stack rather than introducing a separate sync service, message queue, or new API
framework.

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: FastAPI, Starlette, Pydantic Settings, SQLAlchemy 2.x,
Alembic, asyncpg, aiosqlite, httpx, pytest, pytest-asyncio
**Storage**: PostgreSQL for runtime and development, SQLite for automated tests
**Testing**: pytest, FastAPI TestClient/httpx, Ruff, MyPy, Bandit, pip-audit
**Target Platform**: Authenticated JSON API served by the existing FastAPI
application in local Docker Compose and test environments
**Project Type**: Single FastAPI web application with API routes, ORM models,
and server-managed persistence
**Performance Goals**: Device registration and listing requests complete in
under 500 ms for normal local usage, and incremental update retrieval completes
in under 1 second for a device with up to 500 pending change records in a warm
local environment
**Constraints**: No new runtime dependencies, device IDs must match
`[\\w.-]+`, ownership checks must prevent cross-account leakage, API responses
must remain compatible with the documented `/api/2` contracts, and the design
must avoid `# noqa`/`# nosec` shortcut suppressions
**Scale/Scope**: Initial device API only; no device deletion endpoint, no web UI
for device management, no background worker, and no attempt to implement the
entire gpodder sync surface beyond the three requested contracts

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `Spec-First Delivery`: PASS. The feature has a complete spec, this
  implementation plan, and will produce a task breakdown next for traceable
  implementation.
- `Branch Workflow`: PASS. Work is on `005-device-api`, created from `main`, and
  will merge back only through a pull request.
- `Independently Valuable Slices`: PASS. Device registration, device listing,
  and incremental updates remain independently testable and priority ordered,
  with registration and listing providing the MVP foundation.
- `Verification Before Merge`: PASS. The plan defines unit, integration,
  contract, migration, and manual API verification plus the repository quality
  gates required before merge.
- `Strict Python Quality Gates`: PASS. The design stays within Python 3.13 and
  the repository's Ruff, MyPy, Bandit, audit, and pytest tooling without
  relying on inline suppression shortcuts.
- `Security and Simplicity by Default`: PASS. The design extends the existing
  app, auth dependency chain, and database models with only the minimum new
  entities needed for per-user devices and sync snapshots.

## Delivery Workflow

- **Base Branch**: `main`
- **Working Branch**: `005-device-api` created from `main`
- **Commit Convention**: Conventional Commits required for every commit
- **Merge Policy**: Open a pull request after implementation and verification are complete

## Project Structure

### Documentation (this feature)

```text
specs/005-device-api/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── device-api.openapi.yaml
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
│   ├── health.py
│   ├── profile.py
│   └── site.py
├── services/
│   ├── auth.py
│   ├── devices.py
│   ├── localization.py
│   └── readiness.py
└── main.py

alembic/
└── versions/
    └── 0003_device_sync_entities.py

tests/
├── contract/
│   ├── test_auth_api.py
│   └── test_device_api.py
├── integration/
│   └── test_device_updates_api.py
└── unit/
    └── test_device_service.py
```

**Structure Decision**: Keep the existing single `app/` FastAPI project and add
one focused API route module, one device-oriented service module, a small set of
new ORM models for devices and sync-domain records, matching Pydantic schemas,
and one Alembic migration. Tests remain split into unit, integration, and
contract suites so device validation rules, ownership checks, and API
compatibility stay independently traceable.

## Complexity Tracking

No constitution violations identified for this plan.
