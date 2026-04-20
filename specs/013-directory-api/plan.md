# Implementation Plan: Directory API

**Branch**: `013-directory-api` | **Date**: 2026-04-20 | **Spec**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/013-directory-api/spec.md`
**Input**: Feature specification from `/Users/eliassoares/Documents/projects/personal/malipod/specs/013-directory-api/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Expose a public Directory API backed only by the server’s local subscription
catalog (no external directory source). Provide search and toplist endpoints with
JSON/OPML/TXT outputs, plus public tag browsing and metadata lookup endpoints for
podcasts and episodes. Enforce `count`/`number` bounds (1–100), compute subscriber
counts as distinct users per feed, and build `mygpo_link` using the server’s
configured base URL.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.13
**Primary Dependencies**: FastAPI + Starlette, Pydantic Settings, SQLAlchemy 2.x (existing stack)
**Storage**: PostgreSQL (runtime/dev), SQLite (tests); feature is read-only but performs DB reads
**Testing**: pytest + FastAPI `TestClient`, Ruff, MyPy (strict), Bandit, pip-audit
**Target Platform**: Server (Uvicorn/FastAPI)
**Project Type**: Web service (gpodder-compatible API + web pages)
**Performance Goals**: Efficient queries for search/toplist/tag listing (no N+1; paginate/limit via `count`/`number`)
**Constraints**: Public endpoints; no authentication; strict input validation for `count`/`number` and required query params; no DB writes
**Scale/Scope**: Implement endpoints in spec with JSON/OPML/TXT formats; tests required for contract + edge cases

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `Spec-First Delivery`: Spec lives at `/Users/eliassoares/Documents/projects/personal/malipod/specs/013-directory-api/spec.md`.
  Plan lives at `/Users/eliassoares/Documents/projects/personal/malipod/specs/013-directory-api/plan.md`.
  `/speckit.tasks` will generate a task list tracing user stories (P1–P3) to endpoints and tests.
- `Branch Workflow`: Confirm the work will be implemented on a feature branch
  created from `main`, not directly on `main` (`013-directory-api`).
- `Independently Valuable Slices`: Confirm user stories are independently testable,
  priority ordered, and the first slice can stand as the MVP (P1: `/search.*`).
- `Verification Before Merge`: Define the exact tests, checks, and manual
  validation needed for this feature:
  - Automated: contract tests for `search`, `toplist`, `tags`, `tag`, `data/podcast`, `data/episode`, and 400/404 cases.
  - Repo checks: `make check` and `make test`.
  - Manual: run server locally and `curl` a couple of endpoints to confirm content-type and formatting (`.json`, `.opml`, `.txt`).
- `Strict Python Quality Gates`: List the affected Ruff, MyPy, Bandit, audit, and
  pytest commands required for this work:
  - `uv run ruff check .`
  - `uv run mypy .`
  - `uv run bandit -r . -c pyproject.toml`
  - `uv run pip-audit`
  - `uv run pytest` (or `make test`)
  Implementation does not rely on `# noqa` / `# nosec`.
- `Security and Simplicity by Default`: Justify any new dependency, persistence
  choice, external integration, or added architectural layer.
  - No new external integrations are introduced.
  - If tags are not currently stored, the simplest compliant approach is to extend existing podcast feed metadata storage (no new table) so tags can be derived locally without fetching RSS at request time.

## Delivery Workflow

- **Base Branch**: `main`
- **Working Branch**: `013-directory-api` created from `main`
- **Commit Convention**: Conventional Commits required for every commit
- **Merge Policy**: Open a pull request after implementation and verification are complete

## Project Structure

### Documentation (this feature)

```text
specs/013-directory-api/
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
│   ├── deps.py
│   └── routes/
│       └── (new) directory_api.py
├── core/
│   ├── config.py
│   └── security.py
├── db/
│   └── models/
│       └── podcast.py
├── schemas/
│   └── (new) directory.py
└── services/
    ├── subscription_formats.py
    └── (new) directory.py

tests/
├── contract/
│   └── (new) test_directory_api.py
└── integration/
    └── (optional) test_directory_api_flow.py
```

**Structure Decision**: Use the existing `app/` + `tests/` layout. Implement the
Directory API as a dedicated router under `app/api/routes/` with a small service
layer under `app/services/` for DB queries and output shaping.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | No constitution violations | No added architectural layers beyond a small query service |
