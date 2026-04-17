# Implementation Plan: Settings API

**Branch**: `009-settings-api` | **Date**: 2026-04-17 | **Spec**: [/Users/eliassoares/Documents/projects/personal/malipod/specs/009-settings-api/spec.md](/Users/eliassoares/Documents/projects/personal/malipod/specs/009-settings-api/spec.md)
**Input**: Feature specification from `/specs/009-settings-api/spec.md`

**Note**: This plan delivers the gpodder-compatible settings endpoints on top of
the existing FastAPI, SQLAlchemy, and Alembic stack by adding one authenticated
JSON API surface plus scoped settings persistence for account, device, podcast,
and episode targets.

## Summary

Deliver the Settings API as an authenticated read/write compatibility surface
for scope-specific key-value documents. The implementation will add
`GET /api/2/settings/{username}/{scope}.json` and
`POST /api/2/settings/{username}/{scope}.json`, validate scope-specific query
parameters, and persist one JSON settings document per user-owned target. The
design reuses the current HTTP Basic ownership pattern, existing user/device/
podcast/episode domain models, and repository tooling while introducing a
focused settings service plus normalized target-resolution helpers instead of a
new subsystem.

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: FastAPI, Starlette, Pydantic Settings, SQLAlchemy 2.x, Alembic, asyncpg, aiosqlite, httpx, pytest, pytest-asyncio
**Storage**: PostgreSQL for runtime and development, SQLite for automated tests
**Testing**: pytest, FastAPI TestClient/httpx, Ruff, MyPy, Bandit, pip-audit
**Target Platform**: Authenticated compatibility API served by the existing FastAPI application in local Docker Compose and test environments
**Project Type**: Single FastAPI web application with ORM-backed persistence and contract-focused API routes
**Performance Goals**: Settings reads should complete in under 250 ms for a warm local request, and settings writes for any one scope should complete in under 500 ms while returning the full resulting document
**Constraints**: No new runtime dependencies, both endpoints require authentication, scope-specific identifiers must be validated before persistence, write operations must not allow cross-account access, JSON values must round-trip without lossy coercion, and the implementation must not rely on `# noqa`, `# nosec`, or similar inline suppressions
**Scale/Scope**: Initial compatibility surface only; supports four scopes (`account`, `device`, `podcast`, `episode`), one JSON document per scope target, known-setting key preservation, and no website privacy-toggle side effects beyond storing and exposing the documented values

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `Spec-First Delivery`: PASS. The feature has a completed spec, this plan, and
  will produce tasks mapped to authenticated reads, authenticated writes, and
  scope-validation slices.
- `Branch Workflow`: PASS. Work is on `009-settings-api`, created from `main`,
  and will return through the normal pull-request path.
- `Independently Valuable Slices`: PASS. Reading settings, saving settings, and
  enforcing scope-specific target rules are independently testable and
  priority-ordered, with authenticated reads plus writes forming the MVP.
- `Verification Before Merge`: PASS. The plan defines unit, contract,
  integration, migration, and manual API validation for scope resolution, JSON
  round-tripping, key removal, malformed payload handling, and cross-account
  protection before merge.
- `Strict Python Quality Gates`: PASS. The implementation stays within the
  repository's Python 3.13 toolchain and requires `uv run ruff check .`,
  `uv run mypy app tests`, `uv run bandit -r . -c pyproject.toml`,
  `uv run pip-audit`, and `uv run pytest -q` without suppression shortcuts.
- `Security and Simplicity by Default`: PASS. The design adds no runtime
  dependencies, reuses current auth and domain models, and stores one JSON
  document per scope target instead of introducing a more complex key-row or
  polymorphic-settings subsystem.

## Delivery Workflow

- **Base Branch**: `main`
- **Working Branch**: `009-settings-api` created from `main`
- **Commit Convention**: Conventional Commits required for every commit
- **Merge Policy**: Open a pull request after implementation and verification are complete

## Project Structure

### Documentation (this feature)

```text
specs/009-settings-api/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── settings-api.openapi.yaml
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
│       ├── settings_api.py
│       ├── subscriptions_api.py
│       ├── health.py
│       ├── profile_site.py
│       └── site.py
├── core/
│   ├── config.py
│   ├── logging.py
│   ├── localization.py
│   └── security.py
├── db/
│   ├── base.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── device.py
│   │   ├── foundation.py
│   │   ├── podcast.py
│   │   ├── session.py
│   │   ├── settings.py
│   │   └── user.py
│   └── session.py
├── schemas/
│   ├── auth.py
│   ├── device.py
│   ├── episode.py
│   ├── health.py
│   ├── podcast_list.py
│   ├── profile.py
│   ├── setting.py
│   ├── site.py
│   └── subscription.py
├── services/
│   ├── auth.py
│   ├── devices.py
│   ├── episodes.py
│   ├── podcast_lists.py
│   ├── settings.py
│   ├── subscription_formats.py
│   ├── subscriptions.py
│   ├── localization.py
│   └── readiness.py
└── main.py

alembic/
└── versions/
    └── 0007_settings_api.py

tests/
├── contract/
│   ├── test_auth_api.py
│   ├── test_device_api.py
│   ├── test_episodes_api.py
│   ├── test_foundation_api.py
│   ├── test_lists_api.py
│   ├── test_settings_api.py
│   └── test_subscriptions_api.py
├── integration/
│   ├── test_app_startup.py
│   ├── test_device_updates_api.py
│   ├── test_episodes_sync_api.py
│   ├── test_lists_api_flow.py
│   ├── test_settings_api_flow.py
│   ├── test_site_home.py
│   └── test_subscriptions_sync_api.py
└── unit/
    ├── test_device_service.py
    ├── test_episode_service.py
    ├── test_podcast_list_service.py
    ├── test_setting_service.py
    ├── test_subscription_formats.py
    └── test_subscription_service.py
```

**Structure Decision**: Keep the existing single `app/` FastAPI project and add
one dedicated settings route module, one service module for scope resolution and
document mutation, one schema module for request/response validation, and one
migration that adds focused settings persistence. A new `app/db/models/settings.py`
module centralizes the four settings tables because the feature spans user,
device, feed, and episode targets; this keeps the persistence logic cohesive
without overloading unrelated domain-model modules. Tests remain split into
unit, integration, and contract suites so scope rules, JSON mutation behavior,
and endpoint compatibility stay isolated and traceable.

## Phase 0 Research Focus

- Confirm the simplest persistence model for one mutable JSON document per
  scope target while preserving relational integrity for devices, podcasts, and
  episodes.
- Decide how scope target resolution should reuse existing user, device, feed,
  and episode entities instead of introducing synthetic identifiers.
- Define how missing settings documents differ from missing scope targets so the
  API returns `{}` for valid empty scopes but `404` for invalid referenced
  targets.
- Choose where to place the settings models so SQLAlchemy metadata discovery
  stays explicit and easy to review.

## Phase 1 Design Direction

- Add a dedicated `settings.py` model module with four scoped tables:
  `AccountSettingModel`, `DeviceSettingModel`, `PodcastSettingModel`, and
  `EpisodeSettingModel`, each storing a JSON object plus timestamps and a
  uniqueness constraint on its target.
- Reuse `UserModel`, `DeviceModel`, `PodcastFeedModel`, and `EpisodeModel` as
  canonical scope targets so account, device, podcast, and episode settings
  stay linked to the same entities already used by subscriptions and episodes.
- Implement one `SettingsService` that resolves scope targets, creates missing
  settings documents lazily for valid targets, applies `set` and `remove`
  mutations atomically, and returns the final JSON object after each write.
- Add one `settings_api.py` router under `/api/2` that follows the current
  HTTP Basic ownership pattern from subscriptions and episodes, validates scope
  and query parameters through Pydantic schemas, and maps domain errors to
  compatibility HTTP responses.

## Verification Strategy

- Contract tests for:
  - `GET /api/2/settings/{username}/account.json`
  - `POST /api/2/settings/{username}/account.json`
  - `GET /api/2/settings/{username}/{scope}.json` with scope-specific query parameters
  - `POST /api/2/settings/{username}/{scope}.json` with scope-specific query parameters
- Unit tests for:
  - scope validation and required query parameter rules
  - JSON document mutation semantics for `set` and `remove`
  - removal of unknown keys leaving other values unchanged
  - round-tripping nested JSON values without coercion
  - target resolution for device, podcast, and episode scopes
- Integration tests for:
  - create-or-update account settings then read them back
  - device settings for an existing device target
  - podcast and episode settings against existing feed and episode entities
  - cross-account denial, malformed payload handling, and missing-target behavior
- Repository quality gates:
  - `uv run ruff check .`
  - `uv run mypy app tests`
  - `uv run bandit -r . -c pyproject.toml`
  - `uv run pip-audit`
  - `uv run pytest -q`
- Manual validation:
  - curl-driven account scope read and write
  - one device-scope write followed by read
  - one podcast-scope write followed by read
  - one episode-scope write followed by read
  - one missing query parameter case and one cross-account denial case

## Complexity Tracking

No constitution violations identified for this plan.
