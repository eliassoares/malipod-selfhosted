# Implementation Plan: User Metrics

**Branch**: `020-user-metrics` | **Date**: 2026-04-23 | **Spec**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/020-user-metrics/spec.md`
**Input**: Feature specification from `/Users/eliassoares/Documents/projects/personal/malipod/specs/020-user-metrics/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Add a new authenticated user metrics page at `/user/{nickname}/stats`, plus
incremental metric enhancements to the existing podcast and episode pages:

- Podcast header: completion rate, episodes in progress, last played date
- Episode detail: textual progress values, play count + first/last play timestamps,
  and “favorited at” when favorited
- Navigation: add “Metrics” between Subscriptions and Logout

The approach uses existing persisted user listening data (episode action events,
latest progress snapshot, and favorites) and computes explainable aggregates with
clear empty states and strict cross-account privacy.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.13
**Primary Dependencies**: FastAPI, Starlette, Jinja2, Pydantic Settings, SQLAlchemy 2.x, Alembic
**Storage**: PostgreSQL (runtime/dev), SQLite (tests)
**Testing**: pytest, pytest-asyncio, FastAPI TestClient, sqlite3 seeding in integration tests
**Target Platform**: Linux server (web app), local dev on macOS
**Project Type**: web-service + server-rendered site (Jinja2)
**Performance Goals**: Metrics pages render fast for personal usage (hundreds of episodes/events)
**Constraints**: Multi-lingual UI; mobile-friendly templates; no new build step; no cross-account data leaks
**Scale/Scope**: Single-user dashboard + per-podcast/per-episode metrics; best-effort temporal sections

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `Spec-First Delivery`: Confirm the feature has a spec, plan, and task flow that
  preserves traceability from user story to implementation.
- ✅ Spec created at `/Users/eliassoares/Documents/projects/personal/malipod/specs/020-user-metrics/spec.md` and this plan will generate research/design artifacts under the same directory.
- `Branch Workflow`: Confirm the work will be implemented on a feature branch
  created from `main`, not directly on `main`.
- ✅ Branch: `020-user-metrics` created from `main`.
- `Independently Valuable Slices`: Confirm user stories are independently testable,
  priority ordered, and the first slice can stand as the MVP.
- ✅ US1 (user stats page) is independently valuable; US2/US3 are page-level improvements.
- `Verification Before Merge`: Define the exact tests, checks, and manual
  validation needed for this feature; explain any area with no automated coverage
  and what the pull request must include before merge.
- Automated verification:
  - Integration tests for `/user/{nick}/stats`, `/podcast/{id}` header metrics, and `/episode/{id}` metric rendering.
  - Existing quality gates: `uv run pytest`, `uv run ruff check .`, `uv run mypy .`, `uv run bandit -r app -c pyproject.toml`, `uv run pip-audit`.
- Manual validation (best-effort, optional): open pages in browser and validate layout on mobile width.
- `Strict Python Quality Gates`: List the affected Ruff, MyPy, Bandit, audit, and
  pytest commands required for this work. Confirm the implementation plan does
  not rely on `# noqa`, `# nosec`, or similar inline suppressions as a shortcut;
  if an exception is unavoidable, document why the warning is incorrect and how
  review will verify it.
- ✅ No inline waivers planned; fix issues at the root.
- `Security and Simplicity by Default`: Justify any new dependency, persistence
  choice, external integration, or added architectural layer.
- ✅ No new dependencies or persistence planned; metrics are derived from existing tables/services.

**Post-Design Re-check (after Phase 1)**: No new dependencies or storage were introduced by the design artifacts; slices remain independently testable; verification plan remains unchanged.

## Delivery Workflow

- **Base Branch**: `main`
- **Working Branch**: `020-user-metrics` created from `main`
- **Commit Convention**: Conventional Commits required for every commit
- **Merge Policy**: Open a pull request after implementation and verification are complete

## Project Structure

### Documentation (this feature)

```text
specs/020-user-metrics/
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
├── integration/
└── unit/
```

**Structure Decision**: Use the existing server-rendered site architecture under
`app/api/routes/*` + `app/services/*` + `app/templates/*`, with integration tests
under `tests/integration/*` using TestClient and sqlite3 seeding.

## Complexity Tracking

No constitution violations anticipated for this feature.
