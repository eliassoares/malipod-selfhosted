# Implementation Plan: User Authentication and Localized Profile

**Branch**: `004-user-auth` | **Date**: 2026-04-15 | **Spec**: [/Users/eliassoares/Documents/projects/personal/malipod/specs/004-user-auth/spec.md](/Users/eliassoares/Documents/projects/personal/malipod/specs/004-user-auth/spec.md)
**Input**: Feature specification from `/specs/004-user-auth/spec.md`

**Note**: This plan adds Malipod's first account capabilities on top of the
existing FastAPI foundation by introducing website registration and profile
flows, API-compatible login/logout, database-backed sessions, and a reusable
localization layer for English, Spanish, and Portuguese.

## Summary

Deliver the first authenticated Malipod experience with a website registration
flow, a website and API login/logout flow, and an authenticated profile page
addressed by public nickname. The design extends the existing single-app
FastAPI structure with account models, database-backed session tracking, secure
password derivation using the Python standard library, and reusable server-side
template building blocks that support explicit multilingual rendering. The plan
keeps the implementation intentionally small by reusing the current FastAPI,
Jinja2, SQLAlchemy, and Alembic stack rather than introducing a separate auth
service, SPA frontend, or external i18n dependency.

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: FastAPI, Starlette, Jinja2, Pydantic Settings,
SQLAlchemy 2.x, Alembic, asyncpg, aiosqlite, httpx, pytest, pytest-asyncio
**Storage**: PostgreSQL for runtime and development, SQLite for automated tests
**Testing**: pytest, FastAPI TestClient/httpx, Ruff, MyPy, Bandit, pip-audit
**Target Platform**: Server-rendered web application plus JSON API in Docker
Compose local development on macOS/Linux
**Project Type**: Single FastAPI web application with HTML templates and API
routes
**Performance Goals**: Registration and login requests complete in under 1
second for normal local usage, and profile page rendering completes in under 1
second after authentication on a warm local environment
**Constraints**: Pinned dependencies only, Python standard-library password
derivation, DB-backed session invalidation, no `# noqa`/`# nosec` shortcut
suppressions, explicit supported locales (`en`, `es`, `pt-BR`), mobile-first
layouts that also work on desktop
**Scale/Scope**: Initial account foundation only; no password-reset flow,
social login, email verification, admin moderation, public profile editing API,
or generalized CMS localization in this phase

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `Spec-First Delivery`: PASS. The feature has a complete spec, this
  implementation plan, and will produce a traceable task breakdown next.
- `Branch Workflow`: PASS. Work is on `004-user-auth`, created from `main`, and
  will merge back only through a pull request.
- `Independently Valuable Slices`: PASS. Registration, login/logout, and the
  localized profile flow can each be validated as independent slices, with
  registration and login constituting the MVP.
- `Verification Before Merge`: PASS. The plan defines unit, integration,
  contract, responsive-manual, and localization verification plus the standard
  repository quality gates.
- `Strict Python Quality Gates`: PASS. The design stays within Python 3.13,
  current repository tooling, and avoids reliance on inline suppressions as a
  shortcut. Existing suppressions touched by this feature should be refactored
  away rather than copied forward.
- `Security and Simplicity by Default`: PASS. The design uses the existing
  application, database, and templating stack; adds only the minimum account and
  session entities needed; and uses explicit validation and generic auth errors
  to reduce avoidable risk.

## Delivery Workflow

- **Base Branch**: `main`
- **Working Branch**: `004-user-auth` created from `main`
- **Commit Convention**: Conventional Commits required for every commit
- **Merge Policy**: Open a pull request after implementation and verification are complete

## Project Structure

### Documentation (this feature)

```text
specs/004-user-auth/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── auth-api.openapi.yaml
└── tasks.md
```

### Source Code (repository root)

```text
app/
├── api/
│   ├── deps.py
│   └── routes/
│       ├── auth_api.py
│       ├── auth_site.py
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
│   │   ├── foundation.py
│   │   ├── session.py
│   │   └── user.py
│   └── session.py
├── schemas/
│   ├── auth.py
│   ├── health.py
│   ├── profile.py
│   └── site.py
├── services/
│   ├── auth.py
│   ├── localization.py
│   └── readiness.py
├── templates/
│   ├── auth/
│   │   ├── login.html
│   │   └── register.html
│   ├── profile/
│   │   └── detail.html
│   ├── partials/
│   │   ├── footer.html
│   │   ├── head.html
│   │   └── topbar.html
│   ├── base.html
│   └── home.html
└── main.py

alembic/
└── versions/
    └── 0002_user_auth_entities.py

tests/
├── contract/
│   └── test_auth_api.py
├── integration/
│   ├── test_auth_pages.py
│   ├── test_auth_sessions.py
│   └── test_profile_page.py
└── unit/
    ├── test_auth_service.py
    ├── test_localization.py
    └── test_user_validation.py
```

**Structure Decision**: Keep the existing single `app/` FastAPI project and add
focused modules for account routes, auth services, localization, new schemas,
and new ORM models. Templates are split into `auth/`, `profile/`, and reusable
`partials/` so the existing server-rendered approach scales without introducing
frontend build complexity. Tests remain divided into unit, integration, and
contract suites to keep auth rules, page behavior, and API compatibility
traceable.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Database-backed session entity | The API logout contract requires removing a session ID from persistent state | A signed cookie-only session would not satisfy explicit server-side invalidation |
