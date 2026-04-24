# Quickstart: Centralized Subscriptions Sync

**Feature**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/022-centralized-subscriptions-sync/spec.md`
**Date**: 2026-04-24

## Local Manual Validation (Optional)

1. Create a user and two devices using existing flows.
2. Subscribe to different feeds on each device.
3. Toggle “Sincronização centralizada” on the profile page.
4. Verify:
   - `GET /api/2/subscriptions/{user}/{device}.json` returns the union of feeds
   - `GET /api/2/subscriptions/{user}/{device}.opml` returns the same union
5. Toggle off and verify device-scoped behavior returns.

## Automated Verification

- `uv run pytest -q tests/contract/test_subscriptions_api.py`
- `uv run pytest -q tests/integration/test_profile_page.py`
- Full gates before PR:
  - `uv run pytest`
  - `uv run ruff check .`
  - `uv run mypy .`
  - `uv run bandit -r app -c pyproject.toml`
  - `uv run pip-audit`
