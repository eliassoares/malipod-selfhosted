# PR Summary: Device API

## What Changed

- Added `devices`, `podcast_feeds`, `device_subscriptions`, `episodes`, and
  `episode_actions` persistence with Alembic migration support.
- Added authenticated Device API endpoints for device create/update, account
  device listing, and device-specific incremental updates.
- Added device ID and `since` validation helpers plus shared Device API schemas
  and service-layer ownership enforcement.
- Added automated tests covering device validation, service behavior, API
  contracts, incremental updates, and cross-account denial paths.
- Added `make test-device` and `make verify-device` shortcuts for focused local
  verification.

## Verification

- `make test-device` -> `18 passed`
- `uv run pytest tests/unit/test_device_service.py tests/contract/test_device_api.py tests/integration/test_device_updates_api.py -q` -> `18 passed`

## Manual Checks

- Valid device creation and partial updates verified with HTTP Basic
  authentication.
- Cross-account device registration attempts verified as forbidden.
- Device listing verified for populated and empty account states.
- Incremental update retrieval verified for initial sync, `since` filtering,
  optional action inclusion, and unknown-device `404` handling.

## Notes

- Existing non-device suppressions outside the feature scope were not expanded.
- The Device API reuses the existing authentication/session configuration and
  introduces no new runtime environment variables.
