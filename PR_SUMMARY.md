# Settings API PR Summary

## Implemented Scope

- Added authenticated compatibility endpoints for:
  - `GET /api/2/settings/{username}/{scope}.json`
  - `POST /api/2/settings/{username}/{scope}.json`
- Supported all four scopes:
  - `account`
  - `device`
  - `podcast`
  - `episode`
- Added scoped JSON persistence tables and ORM models for account, device,
  podcast, and episode settings
- Implemented lazy document creation for valid targets and `{}` responses for
  valid empty scopes
- Added strict query validation, cross-account protection, and target-not-found
  handling
- Preserved arbitrary JSON values and known setting keys such as
  `public_profile`, `store_user_agent`, `public_subscriptions`,
  `public_subscription`, and `is_favorite`

## Verification

- `uv run ruff check app tests alembic`
- `uv run mypy app tests`
- `uv run bandit -r . -c pyproject.toml`
- `uv run pip-audit`
- `uv run pytest -q`
- `uv run pytest tests/unit/test_setting_service.py tests/contract/test_settings_api.py tests/integration/test_settings_api_flow.py tests/integration/test_app_startup.py -q`

## Migration Notes

- Added Alembic revision `0007_settings_api`
- Introduced new tables:
  - `account_settings`
  - `device_settings`
  - `podcast_settings`
  - `episode_settings`

## Follow-ups

- If website-side behavior should react to known settings like
  `public_profile` or `is_favorite`, that can be layered on top of this stored
  compatibility surface in a future feature.
