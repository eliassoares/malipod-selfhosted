# Implementation Plan: Centralized Subscriptions Sync

**Branch**: `022-centralized-subscriptions-sync` | **Date**: 2026-04-24 | **Spec**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/022-centralized-subscriptions-sync/spec.md`
**Input**: Feature specification from `/Users/eliassoares/Documents/projects/personal/malipod/specs/022-centralized-subscriptions-sync/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Add a per-user preference `centralize_sync` and use it to switch the gpodder
subscriptions reads between:

- Default (off): device-scoped active subscriptions/deltas
- Centralized (on): distinct union of active subscriptions across all devices
  and delta semantics that remove only when the feed is absent from all active
  devices at read time

Also add a profile UI toggle to control the preference.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.13
**Primary Dependencies**: FastAPI, Starlette, Jinja2, Pydantic Settings, SQLAlchemy 2.x, Alembic
**Storage**: PostgreSQL (runtime/dev), SQLite (tests)
**Testing**: pytest, pytest-asyncio, FastAPI TestClient (contract + integration)
**Target Platform**: Linux server (web app), local dev on macOS
**Project Type**: web-service + server-rendered site (Jinja2)
**Performance Goals**: Keep subscription reads fast for typical users (few devices, hundreds of feeds)
**Constraints**: Protocol compatibility; centralized affects reads only; strict cross-account isolation
**Scale/Scope**: Subscriptions endpoints + profile toggle; episode actions out of scope

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `Spec-First Delivery`: Confirm the feature has a spec, plan, and task flow that
  preserves traceability from user story to implementation.
- ✅ Spec at `/Users/eliassoares/Documents/projects/personal/malipod/specs/022-centralized-subscriptions-sync/spec.md`, plan/tasks under the same directory.
- `Branch Workflow`: Confirm the work will be implemented on a feature branch
  created from `main`, not directly on `main`.
- ✅ Branch: `022-centralized-subscriptions-sync` created from `main`.
- `Independently Valuable Slices`: Confirm user stories are independently testable,
  priority ordered, and the first slice can stand as the MVP.
- ✅ US1 (toggle) is independently testable; US2 and US3 add incremental protocol behavior.
- `Verification Before Merge`: Define the exact tests, checks, and manual
  validation needed for this feature; explain any area with no automated coverage
  and what the pull request must include before merge.
- Automated verification:
  - Contract tests for subscriptions endpoints in both modes (JSON + OPML + delta semantics).
  - Integration test for profile toggle persistence.
  - Quality gates: `uv run pytest`, `uv run ruff check .`, `uv run mypy .`, `uv run bandit -r app -c pyproject.toml`, `uv run pip-audit`.
- `Strict Python Quality Gates`: List the affected Ruff, MyPy, Bandit, audit, and
  pytest commands required for this work. Confirm the implementation plan does
  not rely on `# noqa`, `# nosec`, or similar inline suppressions as a shortcut;
  if an exception is unavoidable, document why the warning is incorrect and how
  review will verify it.
- ✅ No inline waivers planned; fix issues at the root.
- `Security and Simplicity by Default`: Justify any new dependency, persistence
  choice, external integration, or added architectural layer.
- ✅ Only adds a boolean column on users; reuses existing services/tables and minimal query changes.

**Post-Design Re-check (after Phase 1)**: Design introduces only a boolean user flag and reuses existing tables; stories remain independently testable; verification plan remains unchanged.

## Delivery Workflow

- **Base Branch**: `main`
- **Working Branch**: `022-centralized-subscriptions-sync` created from `main`
- **Commit Convention**: Conventional Commits required for every commit
- **Merge Policy**: Open a pull request after implementation and verification are complete

## Project Structure

### Documentation (this feature)

```text
specs/022-centralized-subscriptions-sync/
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

**Structure Decision**: Reuse existing API routes in `app/api/routes/` and services
in `app/services/`. Add a DB migration via Alembic and extend contract/integration
tests under `tests/contract/` and `tests/integration/`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations anticipated for this feature.
