# Quickstart: Podcast Detail Page

**Feature**: `specs/018-podcast-detail-page/spec.md`
**Created**: 2026-04-22

## Run locally

- Start the app using the existing project workflow (docker-compose or `uv` as
  used elsewhere in the repo).

## Manual checks

1. Log in with an existing account.
2. Open the subscriptions page and confirm it still renders normally.
3. Open `/podcast/{id}` for a known podcast feed id:
   - Metadata renders with placeholders when images are missing.
   - Episode list renders and can be sorted by date (recent/oldest).
4. For a podcast you are not subscribed to:
   - Subscribe action is visible and works.
5. Favorite/unfavorite a podcast:
   - The state persists when reloading the page.
6. Back on subscriptions page, enable “favorites only”:
   - Only favorited podcasts appear.

## Automated checks

Run the repository quality gates before opening a PR:

- `uv run pytest`
- `uv run ruff check .`
- `uv run mypy .`
- `uv run bandit -r app -c pyproject.toml`
