# MaliPod — Claude Code Guidelines

## Project

Self-hosted gpodder.net-compatible podcast sync server with a full web UI.

- **Stack**: Python 3.13, FastAPI, SQLAlchemy 2.x (async), Alembic, Pydantic Settings, Jinja2 + Tailwind CSS
- **DB**: PostgreSQL (prod/dev) · SQLite via aiosqlite (tests only)
- **Auth**: Basic Auth for API endpoints · session cookies for the web UI
- **Tests**: `uv run pytest` — unit / contract / integration (323 tests)
- **Quality gates**: `uv run ruff check .` · `uv run mypy .` · `uv run bandit -r app -c pyproject.toml` · `uv run pip-audit`

## Architecture

```
app/
  api/
    routes/          # FastAPI routers (*_api.py = gpodder API, *_site.py = web UI)
    deps.py          # FastAPI dependency injection
    utils.py         # Shared helpers (e.g. apply_locale_cookie)
  core/
    config.py        # Pydantic Settings
    localization.py  # EN / ES / PT-BR translation catalogs
    security.py      # Password hashing, token helpers
    time_format.py   # Compact duration formatter
  db/
    models/          # SQLAlchemy ORM models
    session.py       # Async engine + session factory
  services/          # Business logic (one service class per domain)
  schemas/           # Pydantic schemas (request / response / page context)
  templates/         # Jinja2 HTML templates (base.html + partials + pages)
  static/            # CSS, fonts, placeholder images
alembic/versions/    # Database migrations (0001 … 0015)
tests/
  unit/              # Pure logic, no DB
  contract/          # HTTP-level API contract tests (TestClient + Basic Auth)
  integration/       # Full page / flow tests (TestClient + session cookies)
specs/               # Feature specs, plans, and task checklists
```

## Conventions

- **Commit style**: Conventional Commits (`feat`, `fix`, `refactor`, `docs`, etc.)
- **Line length**: 88 chars (ruff)
- **Branch naming**: `NNN-feature-name` matching the spec directory number
- **Specs**: `specs/NNN-feature-name/` — spec.md, plan.md, tasks.md, research.md, data-model.md
- **Site routers**: always registered with `include_in_schema=False` in `main.py`
- **Locale cookie**: all site GET handlers call `apply_locale_cookie(response, settings, locale)`; cookie takes priority over `user.language_preference` in `resolve_locale`

## Implemented features (web UI)

| Page | Route |
|------|-------|
| Home / landing | `GET /` |
| Registration | `GET/POST /register` |
| Login | `GET/POST /login` |
| Settings (profile) | `GET /user/profile/{nickname}` |
| Subscriptions | `GET /user/subscriptions/{nickname}` |
| Podcast detail | `GET /podcast/{id}` |
| Episode detail | `GET /episode/{id}` |
| Metrics | `GET /user/{nickname}/stats` |

## Implemented gpodder.net API endpoints

Auth, Devices, Subscriptions (delta + replace), Episode Actions, Settings,
Favorites, Podcast Lists, Device Sync, Directory, Suggestions, Client Config,
Health probes. See README for the full table.

## Key migrations

| Revision | Change |
|----------|--------|
| 0001–0007 | Core tables: users, sessions, devices, feeds, episodes, actions, subscriptions |
| 0008 | favorite_episodes |
| 0009 | device_sync_groups |
| 0013 | favorite_podcasts |
| 0014 | episodes.media_url |
| 0015 | users.centralize_sync |

## Testing notes

- Contract tests use HTTP Basic Auth helpers (`register_user`, `create_device`) — no direct SQLite seeding
- Integration tests seed via direct SQLite writes when they need specific DB state (e.g. play events)
- Do not mock the DB in tests — all tests run against an in-process SQLite instance
