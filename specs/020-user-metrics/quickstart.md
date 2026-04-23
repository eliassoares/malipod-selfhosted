# Quickstart: User Metrics

**Feature**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/020-user-metrics/spec.md`
**Date**: 2026-04-23

## Run Locally

- Start the app as usual (local dev settings).
- Visit:
  - `/podcast/{id}` and confirm new header metrics render
  - `/episode/{id}` and confirm textual metrics render
  - `/user/{your_nick}/stats`

## Test

- Run feature-focused tests:
  - `uv run pytest -q tests/integration/test_user_stats_page.py`
  - `uv run pytest -q tests/integration/test_podcast_detail_page.py`
  - `uv run pytest -q tests/integration/test_episode_detail_page.py`

- Run full quality gates before PR:
  - `uv run pytest`
  - `uv run ruff check .`
  - `uv run mypy .`
  - `uv run bandit -r app -c pyproject.toml`
  - `uv run pip-audit`
