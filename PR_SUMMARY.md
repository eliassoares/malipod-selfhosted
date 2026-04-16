# PR Summary

## Scope

- add authenticated `POST /api/2/episodes/{username}.json` uploads for batch
  episode actions with URL sanitation, `play` validation, append-only history,
  and server-issued timestamps
- add authenticated `GET /api/2/episodes/{username}.json` retrieval with
  `since`, `podcast`, `device`, and `aggregated=true` support
- preserve compatibility with existing device updates by refreshing the
  latest-state projection consumed by `/api/2/updates/{username}/{deviceid}.json`

## Verification

- `uv run ruff check .`
- `uv run mypy app tests`
- `uv run bandit -r . -c pyproject.toml`
- `uv run pip-audit`
- `uv run pytest -q`
- `make verify-episodes`

## Migration Notes

- adds `0005_episode_action_history.py`
- creates `episode_action_events` to support append-only episode-action sync
  history while leaving `episode_actions` as the latest-state projection

## Deferred Follow-Ups

- richer action metadata for non-`play` events if future clients need more than
  action type plus timestamp
- optional retention or compaction strategies if episode-action history grows
  substantially for heavy-sync accounts
