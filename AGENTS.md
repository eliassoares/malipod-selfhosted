# malipod Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-04-18

## Active Technologies
- Python 3.13 + FastAPI, Starlette, Jinja2, Pydantic Settings, (004-user-auth)
- PostgreSQL for runtime and development, SQLite for automated tests (004-user-auth)
- Python 3.13 + FastAPI, Starlette, Pydantic Settings, SQLAlchemy 2.x, (005-device-api)
- Python 3.13 + FastAPI, Starlette, Pydantic Settings, SQLAlchemy 2.x, Alembic, asyncpg, aiosqlite, httpx, pytest, pytest-asyncio (009-settings-api)

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
- 011-device-sync-api: Added Python 3.13 + FastAPI, Starlette, Pydantic Settings, SQLAlchemy 2.x, Alembic, asyncpg, aiosqlite, httpx, pytest, pytest-asyncio
- 010-favorites-api: Added Python 3.13 + FastAPI, Starlette, Pydantic Settings, SQLAlchemy 2.x, Alembic, asyncpg, aiosqlite, httpx, pytest, pytest-asyncio
- 009-settings-api: Added Python 3.13 + FastAPI, Starlette, Pydantic Settings, SQLAlchemy 2.x, Alembic, asyncpg, aiosqlite, httpx, pytest, pytest-asyncio


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
