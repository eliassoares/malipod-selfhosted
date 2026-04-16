# PR Summary

## Scope

- add authenticated subscriptions read endpoints for device-scoped and
  account-wide exports in JSON, OPML, plaintext, and JSONP-for-JSON mode
- add full-device subscription uploads with replacement semantics, automatic
  device creation, and empty-body success responses
- add delta upload and delta read synchronization with URL sanitation,
  `update_urls`, and server-issued timestamps backed by subscription change
  history

## Verification

- `uv run ruff check .`
- `uv run mypy app tests`
- `uv run bandit -r . -c pyproject.toml`
- `uv run pip-audit`
- `uv run pytest -q`
- `make verify-subscriptions`

## Migration Notes

- adds `0004_subscription_sync_history.py`
- creates `subscription_change_events` to support incremental subscription sync

## Deferred Follow-Ups

- richer feed metadata preservation during full uploads from metadata-poor
  sources
- possible future account-level sync cursors if clients need non-device-scoped
  subscription history
