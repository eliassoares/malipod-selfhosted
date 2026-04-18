# Implementation Plan: Device Synchronization API

**Branch**: `011-device-sync-api` | **Date**: 2026-04-18 | **Spec**: [/Users/eliassoares/Documents/projects/personal/malipod/specs/011-device-sync-api/spec.md](/Users/eliassoares/Documents/projects/personal/malipod/specs/011-device-sync-api/spec.md)
**Input**: Feature specification from `/specs/011-device-sync-api/spec.md`

**Note**: This plan delivers the gpodder-compatible device synchronization
endpoints for grouping devices into shared-sync sets. The implementation extends
the existing FastAPI + SQLAlchemy stack by adding one new authenticated API
surface (`/api/2/sync-devices/{username}.json`) plus a minimal persistence model
for representing synchronization groups per user.

## Summary

Deliver a Device Synchronization compatibility API that (1) returns a user's
current synchronization grouping and (2) allows clients to start/stop device
synchronization between device IDs. The design reuses the existing authentication
and ownership enforcement (`authenticate_api_user`) and the existing device
registry as the source of truth for device identity. Synchronization groups are
represented as a minimal per-user grouping identifier persisted alongside device
rows, with service-layer validation ensuring only the owning user can create,
merge, or split groups.

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: FastAPI, Starlette, Pydantic Settings, SQLAlchemy 2.x, Alembic, asyncpg, aiosqlite, httpx, pytest, pytest-asyncio
**Storage**: PostgreSQL for runtime and development, SQLite for automated tests
**Testing**: pytest, FastAPI TestClient/httpx, Ruff, MyPy, Bandit, pip-audit
**Target Platform**: Authenticated compatibility API served by the existing FastAPI application in local Docker Compose and test environments
**Project Type**: Single FastAPI web application with ORM-backed persistence and contract-focused API routes
**Performance Goals**: Sync-status GET returns in under 300 ms for a warm local request with up to 100 devices; sync mutation POST completes in under 800 ms locally for common operations (group 2 devices, stop-sync 1 device) and remains stable for up to 200 affected devices
**Constraints**: No new runtime dependencies; requests require authentication; username ownership must be enforced; device IDs must be validated consistently with the existing device API; operations must be idempotent; and the implementation must not rely on `# noqa`, `# nosec`, or similar inline suppressions as shortcuts
**Scale/Scope**: Adds only the device sync grouping surface; no background job, no UI, no cross-user synchronization, no device deletion, and no attempt to implement additional gpodder sync endpoints beyond this contract

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `Spec-First Delivery`: PASS. The feature has a completed spec, this plan, and
  will produce a task breakdown mapping each user story to one independently
  testable implementation slice.
- `Branch Workflow`: PASS. Work is on `011-device-sync-api`, created from `main`,
  and will merge back only through a pull request.
- `Independently Valuable Slices`: PASS. Status retrieval (P1), mutation (P2),
  and hardened error/authorization behavior (P3) remain independently testable,
  with status retrieval as the MVP.
- `Verification Before Merge`: PASS. Verification will include contract and
  integration tests for GET/POST behavior, access control tests for cross-account
  denial, and unit tests for grouping/merge/split behavior. Repository gates:
  `uv run ruff check .`, `uv run mypy app tests`, `uv run bandit -r . -c pyproject.toml`,
  `uv run pip-audit`, and `uv run pytest -q`.
- `Strict Python Quality Gates`: PASS. Implementation will follow existing typed
  service patterns and will not rely on inline suppression waivers.
- `Security and Simplicity by Default`: PASS. The design reuses the existing
  app, auth helpers, and device registry; it adds only the minimal persistence
  required to represent per-user sync groups.

## Delivery Workflow

- **Base Branch**: `main`
- **Working Branch**: `011-device-sync-api` created from `main`
- **Commit Convention**: Conventional Commits required for every commit
- **Merge Policy**: Open a pull request after implementation and verification are complete

## Project Structure

### Documentation (this feature)

```text
specs/011-device-sync-api/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── device-sync-api.openapi.yaml
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
│       ├── settings_api.py
│       ├── subscriptions_api.py
│       ├── sync_devices_api.py          # new
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
│   │   ├── device.py                    # updated (sync group support)
│   │   ├── device_sync_group.py         # new (if introduced as a model)
│   │   ├── foundation.py
│   │   ├── podcast.py
│   │   ├── session.py
│   │   └── user.py
│   └── session.py
├── schemas/
│   ├── auth.py
│   ├── device.py
│   ├── sync_devices.py                  # new
│   └── ...
├── services/
│   ├── auth.py
│   ├── devices.py
│   ├── sync_devices.py                  # new (grouping/mutation logic)
│   └── ...
└── main.py

alembic/
└── versions/
    └── 0009_device_sync_groups.py        # new (name TBD)

tests/
├── contract/
│   └── test_sync_devices_api.py          # new
├── integration/
│   └── test_sync_devices_api_flow.py     # new
└── unit/
    └── test_device_sync_service.py       # new
```

**Structure Decision**: Keep the existing single `app/` FastAPI project. Add one
route module for the sync-devices endpoints, a focused service module that owns
sync group validation and mutation, and minimal ORM/migration changes to persist
per-user group membership. Tests remain split into unit (group logic), contract
(response shapes), and integration (end-to-end flows).

## Complexity Tracking

No constitution violations identified for this plan.
