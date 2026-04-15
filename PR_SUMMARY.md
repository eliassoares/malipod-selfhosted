# PR Summary: User Authentication and Localized Profile

## What Changed

- Added `users` and `authenticated_sessions` persistence with Alembic migration support.
- Added secure registration, login, logout, and session handling for web and compatibility API flows.
- Added localized web experiences for registration, login, and profile pages with shared template partials and cookie-backed language selection.
- Added validation for nickname, email, password confirmation, and supported locales.
- Added automated tests covering validation, auth services, website flows, profile localization, and the compatibility API contract.
- Updated pinned dependencies and lockfile to keep the auth stack free of known vulnerabilities.

## Verification

- `uv run ruff check .`
- `uv run mypy app tests`
- `uv run pytest -q` -> `39 passed`
- `uv run bandit -r . -c pyproject.toml`
- `uv run pip-audit`

## Manual Checks

- Registration page verified with mobile-first layout adapted for desktop rendering.
- Login page verified with generic invalid-login messaging.
- Profile page verified with locale precedence: authenticated user preference overrides stale guest cookie.
- Compatibility API login/logout verified with cookie issuance, mismatch handling, and logout invalidation.

## Notes

- `google_stitch_templates/` remains untracked and was used only as visual reference material.
- Existing non-auth suppressions outside the feature scope were not expanded; auth-related changes were implemented without adding `# noqa` or `# nosec`.
