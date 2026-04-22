# Implementation Plan: Podcast Detail Page

**Branch**: `018-podcast-detail-page` | **Date**: 2026-04-22 | **Spec**: `specs/018-podcast-detail-page/spec.md`
**Input**: Feature specification from `specs/018-podcast-detail-page/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Deliver a new authenticated page at `/podcast/{ID_PODCAST}` that shows podcast
metadata and a sortable list of episodes, with actions to subscribe (when not
subscribed) and to favorite/unfavorite the podcast. Extend the existing
subscriptions page to support filtering to show only favorited podcasts.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.13
**Primary Dependencies**: FastAPI + Starlette, Jinja2Templates, SQLAlchemy 2.x
**Storage**: PostgreSQL (runtime/dev) and SQLite (tests), via SQLAlchemy + Alembic
**Testing**: pytest, pytest-asyncio
**Target Platform**: Web server
**Project Type**: Web application (server-rendered pages + JSON APIs)
**Performance Goals**: Page loads feel responsive for typical episode lists
**Constraints**: No horizontal scroll on mobile; sorting actions remain fast
**Scale/Scope**: Per-user subscriptions and per-podcast episode lists (can be large)

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
- Pass: spec exists at `specs/018-podcast-detail-page/spec.md` and planning artifacts live under `specs/018-podcast-detail-page/`.
- Pass: implementation stays on branch `018-podcast-detail-page` created from `main`.
- Pass: user stories are priority-ordered and independently testable.
- Verification required before merge:
  - Automated: relevant pytest coverage for new site route + favorite filter behavior.
  - Quality gates: `uv run pytest`, `uv run ruff check .`, `uv run mypy .`, `uv run bandit -r app -c pyproject.toml`.
  - Manual: open `/podcast/{id}` on desktop + mobile widths; verify sorting and state changes.
- No inline suppressions planned; address lint/typing/security findings at the source.
- New persistence: add a per-user per-podcast favorite flag; keep it minimal with a dedicated table and uniqueness constraint.

## Delivery Workflow

- **Base Branch**: `main`
- **Working Branch**: `018-podcast-detail-page` created from `main`
- **Commit Convention**: Conventional Commits required for every commit
- **Merge Policy**: Open a pull request after implementation and verification are complete

## Project Structure

### Documentation (this feature)

```text
specs/018-podcast-detail-page/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
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
