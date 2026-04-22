# malipod Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-04-22

## Active Technologies
- Python 3.13 + FastAPI, Starlette, Jinja2, Pydantic Settings, (004-user-auth)
- PostgreSQL for runtime and development, SQLite for automated tests (004-user-auth)
- Python 3.13 + FastAPI, Starlette, Pydantic Settings, SQLAlchemy 2.x, (005-device-api)
- Python 3.13 + FastAPI, Starlette, Pydantic Settings, SQLAlchemy 2.x, Alembic, asyncpg, aiosqlite, httpx, pytest, pytest-asyncio (009-settings-api)
- Python 3.13 + FastAPI + Starlette, Pydantic Settings (existing project stack) (012-client-parametrization)
- N/A (endpoint must not read/write DB) (012-client-parametrization)
- Python 3.13 + FastAPI + Starlette, Pydantic Settings, SQLAlchemy 2.x (existing stack) (013-directory-api)
- PostgreSQL (runtime/dev), SQLite (tests); feature is read-only but performs DB reads (013-directory-api)
- Python 3.13 + FastAPI, Starlette, Pydantic, SQLAlchemy 2.x (014-suggestions-api)
- Python 3.13 + FastAPI, Starlette, Jinja2Templates, Tailwind CDN config (no build step) (015-home-landing)
- PostgreSQL (runtime/dev), SQLite (tests) — *não há mudança de storage* (015-home-landing)
- Python 3.13 + FastAPI, Starlette, Jinja2Templates, SQLAlchemy 2.x, Alembic, Tailwind CDN (sem build step) (017-subscriptions-page)
- Python 3.13 + FastAPI, Starlette, Jinja2Templates, SQLAlchemy 2.x (016-user-data-tools)
- Python 3.13 + FastAPI + Starlette, Jinja2Templates, SQLAlchemy 2.x (018-podcast-detail-page)
- PostgreSQL (runtime/dev) and SQLite (tests), via SQLAlchemy + Alembic (018-podcast-detail-page)

- Python 3.13 + FastAPI, Uvicorn, Pydantic Settings, SQLAlchemy 2.x, (003-podcast-sync-platform)

## Project Structure

```text
app/
tests/
```

## Commands

uv run pytest && uv run ruff check .

## Code Style

Python 3.13: Follow standard conventions

## Recent Changes
- 018-podcast-detail-page: Added Python 3.13 + FastAPI + Starlette, Jinja2Templates, SQLAlchemy 2.x
- 017-subscriptions-page: Added Python 3.13 + FastAPI, Starlette, Jinja2Templates, SQLAlchemy 2.x, Alembic, Tailwind CDN (sem build step)
- 016-user-data-tools: Added Python 3.13 + FastAPI, Starlette, Jinja2Templates, SQLAlchemy 2.x


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
