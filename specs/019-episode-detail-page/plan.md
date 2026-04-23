# Implementation Plan: Episode Detail Page

**Branch**: `019-episode-detail-page` | **Date**: 2026-04-22 | **Spec**: `specs/019-episode-detail-page/spec.md`
**Input**: Feature specification from `specs/019-episode-detail-page/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Deliver a new authenticated episode detail page (based on the Stitch template)
that displays episode metadata and per-user progress, provides actions to
favorite/unfavorite, download when available, and share the episode link, and
optionally shows a listening history section when events exist.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.13
**Primary Dependencies**: FastAPI + Starlette, Jinja2Templates, SQLAlchemy 2.x
**Storage**: PostgreSQL (runtime/dev) and SQLite (tests), via SQLAlchemy + Alembic
**Testing**: pytest, pytest-asyncio, FastAPI TestClient
**Target Platform**: Web server
**Project Type**: Web application (server-rendered pages + JSON APIs)
**Performance Goals**: Page loads feel responsive for typical episodes
**Constraints**: No horizontal scroll on mobile; actions are idempotent and fast
**Scale/Scope**: Per-user progress and favorites; optional listening history per episode

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `Spec-First Delivery`: Confirm the feature has a spec, plan, and task flow that
  preserves traceability from user story to implementation.
- `Branch Workflow`: Confirm the work will be implemented on a feature branch
  created from `main`, not directly on `main`.
- `Independently Valuable Slices`: Confirm user stories are independently testable,
  priority ordered, and the first slice can stand as the MVP.
- `Verification Before Merge`: Define the exact tests, checks, and manual
  validation needed for this feature; explain any area with no automated coverage
  and what the pull request must include before merge.
- `Strict Python Quality Gates`: List the affected Ruff, MyPy, Bandit, audit, and
  pytest commands required for this work. Confirm the implementation plan does
  not rely on `# noqa`, `# nosec`, or similar inline suppressions as a shortcut;
  if an exception is unavoidable, document why the warning is incorrect and how
  review will verify it.
- `Security and Simplicity by Default`: Justify any new dependency, persistence
  choice, external integration, or added architectural layer.

Constitution check (pre-design):
- Pass: spec exists at `specs/019-episode-detail-page/spec.md` and artifacts live under `specs/019-episode-detail-page/`.
- Pass: implementation stays on branch `019-episode-detail-page` created from `main`.
- Pass: user stories are priority-ordered and independently testable.
- Verification required before merge:
  - Automated: pytest coverage for render, 404, favorite toggle, download visibility, share link.
  - Quality gates: `uv run pytest`, `uv run ruff check .`, `uv run mypy .`, `uv run bandit -r app -c pyproject.toml`.
  - Manual: open episode page on desktop + mobile widths; verify progress visualization and action states.
- No inline suppressions planned; address lint/typing/security findings at the source.
- Persistence: reuse existing episode action/progress/favorite tables where possible; avoid adding new tables unless required for “history”.

## Delivery Workflow

- **Base Branch**: `main`
- **Working Branch**: `019-episode-detail-page` created from `main`
- **Commit Convention**: Conventional Commits required for every commit
- **Merge Policy**: Open a pull request after implementation and verification are complete

## Project Structure

### Documentation (this feature)

```text
specs/019-episode-detail-page/
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
│   └── routes/
├── core/
├── db/
│   ├── migrations/
│   └── models/
├── services/
└── templates/

tests/
```

**Structure Decision**: This feature is implemented in the existing FastAPI app
under `app/` with server-rendered templates in `app/templates/` and route
handlers in `app/api/routes/`. Automated tests live under `tests/`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
