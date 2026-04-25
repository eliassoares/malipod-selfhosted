# Implementation Plan: Episode Playlists

**Branch**: `027-episode-playlists` | **Date**: 2026-04-25 | **Spec**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/027-episode-playlists/spec.md`
**Input**: Feature specification from `/Users/eliassoares/Documents/projects/personal/malipod/specs/027-episode-playlists/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Add episode playlists for signed-in users:

- New site pages to manage playlists (list/create/edit/delete) and view playlist details.
- “Favorites” behaves as a special read-only playlist backed by the existing favorites feature.
- Episode detail page gains an “Add to playlist” action that can add the episode to multiple playlists via a popup.
- Playlists are included in user export/import snapshots (metadata + memberships).

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: FastAPI, Starlette, Jinja2Templates, Pydantic Settings, SQLAlchemy 2.x, Alembic
**Storage**: PostgreSQL (runtime/dev), SQLite (tests)
**Testing**: pytest, pytest-asyncio, FastAPI TestClient (contract + integration)
**Target Platform**: Linux server (web app), local dev on macOS
**Project Type**: web-service + server-rendered site (Jinja2)
**Performance Goals**: Playlist pages remain fast for typical users (hundreds–thousands of episodes).
**Constraints**: Must not regress existing favorites behavior or existing user export/import; strict account isolation.
**Scale/Scope**: New playlist tables + 2 site pages + episode detail integration; no gpodder protocol changes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `Spec-First Delivery`: Confirm the feature has a spec, plan, and task flow that
  preserves traceability from user story to implementation.
- ✅ Spec exists at `/Users/eliassoares/Documents/projects/personal/malipod/specs/027-episode-playlists/spec.md`; plan/tasks will live under the same directory.
- `Branch Workflow`: Confirm the work will be implemented on a feature branch
  created from `main`, not directly on `main`.
- ✅ Branch `027-episode-playlists` created from `main`.
- `Independently Valuable Slices`: Confirm user stories are independently testable,
  priority ordered, and the first slice can stand as the MVP.
- ✅ US1 (CRUD/manage playlists) is independently valuable; US2/US3 add details + faster adds.
- `Verification Before Merge`: Define the exact tests, checks, and manual
  validation needed for this feature; explain any area with no automated coverage
  and what the pull request must include before merge.
- Automated verification:
  - Integration tests for playlist site flows (CRUD, owner-only, add/remove episodes).
  - Integration test for episode detail “Add to playlist” flow.
  - Snapshot export/import tests for playlists (round-trip) leveraging existing user data tools tests.
  - Quality gates: `uv run pytest`, `uv run ruff check .`, `uv run mypy .`, `uv run bandit -r app -c pyproject.toml`, `uv run pip-audit`.
- `Strict Python Quality Gates`: List the affected Ruff, MyPy, Bandit, audit, and
  pytest commands required for this work. Confirm the implementation plan does
  not rely on `# noqa`, `# nosec`, or similar inline suppressions as a shortcut;
  if an exception is unavoidable, document why the warning is incorrect and how
  review will verify it.
- ✅ No inline waivers planned; fix issues at the root.
- `Security and Simplicity by Default`: Justify any new dependency, persistence
  choice, external integration, or added architectural layer.
- ✅ Adds two new tables and reuses existing patterns for server-rendered forms, placeholders, and user export/import. No new external dependencies planned.

## Delivery Workflow

- **Base Branch**: `main`
- **Working Branch**: `027-episode-playlists` created from `main`
- **Commit Convention**: Conventional Commits required for every commit
- **Merge Policy**: Open a pull request after implementation and verification are complete

## Project Structure

### Documentation (this feature)

```text
specs/027-episode-playlists/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
app/
├── api/
│   ├── routes/
│   └── deps.py
├── core/
├── db/
│   ├── models/
│   └── session.py
├── services/
└── templates/

tests/
├── contract/
└── integration/
```

**Structure Decision**: Implement as server-rendered site routes under `app/api/routes/`,
business logic in `app/services/`, persistence in `app/db/models/` + Alembic migrations,
templates in `app/templates/`, and integration/contract tests under `tests/`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations anticipated for this feature.
