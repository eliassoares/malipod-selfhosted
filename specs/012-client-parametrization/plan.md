# Implementation Plan: Client Parametrization

**Branch**: `012-client-parametrization` | **Date**: 2026-04-20 | **Spec**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/012-client-parametrization/spec.md`
**Input**: Feature specification from `/Users/eliassoares/Documents/projects/personal/malipod/specs/012-client-parametrization/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Add a public, stateless `GET /clientconfig.json` endpoint so gpodder-compatible
clients can auto-discover the server base URL. The endpoint returns JSON with:
`mygpo.baseurl` (normalized with trailing slash), optional `mygpo-feedservice.baseurl`
for compatibility, and `update_timeout` (seconds) to guide client-side caching.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.13
**Primary Dependencies**: FastAPI + Starlette, Pydantic Settings (existing project stack)
**Storage**: N/A (endpoint must not read/write DB)
**Testing**: pytest + FastAPI `TestClient` (httpx underneath), Ruff, MyPy (strict), Bandit, pip-audit
**Target Platform**: Server (Uvicorn/FastAPI)
**Project Type**: Web service (gpodder-compatible API + web pages)
**Performance Goals**: Negligible overhead (simple in-memory config response; no DB IO)
**Constraints**: Public endpoint, stateless, `application/json`, base URL normalization (single trailing slash)
**Scale/Scope**: One new public endpoint + contract tests; no schema migrations

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `Spec-First Delivery`: Spec lives at `/Users/eliassoares/Documents/projects/personal/malipod/specs/012-client-parametrization/spec.md`.
  Plan lives at `/Users/eliassoares/Documents/projects/personal/malipod/specs/012-client-parametrization/plan.md`.
  `/speckit.tasks` will create tasks that trace back to FRs and acceptance scenarios.
- `Branch Workflow`: Confirm the work will be implemented on a feature branch
  created from `main`, not directly on `main` (`012-client-parametrization`).
- `Independently Valuable Slices`: Confirm user stories are independently testable,
  priority ordered, and the first slice can stand as the MVP (P1 returns `mygpo.baseurl`).
- `Verification Before Merge`: Define the exact tests, checks, and manual
  validation needed for this feature:
  - Automated: new contract test for `GET /clientconfig.json` (no auth; JSON shape; baseurl normalization; `update_timeout` positive).
  - Repo checks: `make check` and `make test` (or `make verify`).
  - Manual: `curl http://localhost:8000/clientconfig.json` returns JSON with normalized `mygpo.baseurl`.
- `Strict Python Quality Gates`: List the affected Ruff, MyPy, Bandit, audit, and
  pytest commands required for this work:
  - `uv run ruff check .`
  - `uv run mypy .`
  - `uv run bandit -r . -c pyproject.toml`
  - `uv run pip-audit`
  - `uv run pytest` (or `make test`)
  Implementation does not rely on `# noqa` / `# nosec`.
- `Security and Simplicity by Default`: Justify any new dependency, persistence
  choice, external integration, or added architectural layer (none planned).

## Delivery Workflow

- **Base Branch**: `main`
- **Working Branch**: `012-client-parametrization` created from `main`
- **Commit Convention**: Conventional Commits required for every commit
- **Merge Policy**: Open a pull request after implementation and verification are complete

## Project Structure

### Documentation (this feature)

```text
specs/012-client-parametrization/
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
│       └── (new) client_config.py
├── core/
│   └── config.py
├── main.py
└── schemas/
    └── (new) client_config.py

tests/
├── contract/
│   └── (new) test_client_config.py
└── conftest.py
```

**Structure Decision**: Use the existing `app/` + `tests/` layout. Implement the
new endpoint as a dedicated router module under `app/api/routes/` and add a
contract test under `tests/contract/`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | No constitution violations | No added complexity required |
