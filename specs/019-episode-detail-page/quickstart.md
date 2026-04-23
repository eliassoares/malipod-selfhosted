# Quickstart: Episode Detail Page

**Feature**: `specs/019-episode-detail-page/spec.md`
**Created**: 2026-04-22

## Manual checks

1. Log in with an existing account.
2. Open a podcast detail page and navigate to an episode (or open `/episode/{id}` directly).
3. Verify:
   - Metadata renders with placeholders when missing.
   - Progress area shows values when progress exists; shows “unknown/empty” state when not.
   - Favorite toggle persists across reload.
   - Download appears only when a downloadable URL exists.
   - Share link is present and points to the episode page.
   - Listening history shows recent events when available; otherwise shows an empty state.

## Automated checks

- `uv run pytest`
- `uv run ruff check .`
- `uv run mypy .`
- `uv run bandit -r app -c pyproject.toml`
