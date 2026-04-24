# PR Summary — Centralized Subscriptions Sync

## What

Adds a per-user preference `centralize_sync` that switches *read* behavior for
gpodder subscriptions:

- **Off (default)**: device-scoped reads and deltas behave exactly as before.
- **On**:
  - `GET /subscriptions/{user}/{device}.{json|opml|txt}` returns the **distinct
    union** of active subscriptions across **all** devices for that user.
  - `GET /api/2/subscriptions/{user}/{device}.json?since=...` (delta) aggregates
    events across **all** devices:
    - `add`: union across devices since `since`
    - `remove`: only returned when the feed is **absent from all active device
      subscriptions** at read time.

Also adds a **Profile** toggle to enable/disable centralized sync.

## DB

- `users.centralize_sync BOOLEAN NOT NULL DEFAULT FALSE` (Alembic `0015`).

## UI

- Profile page: new “Sync” card with a “Centralized sync” checkbox.
- Fully localized (`en`, `es`, `pt-BR`).

## Verification

- `uv run pytest` → **322 passed**
- `uv run ruff check .` → **pass**
- `uv run mypy .` → **pass**
- `uv run bandit -r app -c pyproject.toml` → **no issues**
- `uv run pip-audit` → **no known vulnerabilities**
