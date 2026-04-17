# Quickstart: Favorites API

## Goal

Run the favorites compatibility feature locally, verify authenticated favorite
episode retrieval, and confirm metadata serialization and access control before
opening a pull request.

## Prerequisites

- Docker and Docker Compose available locally
- Project dependencies installed with the pinned toolchain
- Existing auth and episode/feed flows already working in the repository
- At least one development user plus one episode and one favorite projection
  row available for manual validation

## 1. Prepare configuration

1. Ensure your local environment file exists:

   ```bash
   cp .env.example .env
   ```

2. Confirm the application secret and database settings are valid.
3. Create one local development account through the existing auth flow.

## 2. Start the application

1. Start the stack:

   ```bash
   docker compose up --build
   ```

2. Wait for PostgreSQL and the FastAPI app to report healthy.
3. Keep one authenticated username and password available for manual checks.

## 3. Prepare favorite episode data

1. Ensure one episode and its podcast feed exist in the local database.
2. Insert one favorite projection row for the authenticated user through local
   test data, seed tooling, or direct database access used by your development
   workflow.
3. Keep the episode URL, podcast URL, and username available for response
   verification.

## 4. Read favorite episodes

1. Request the user's favorites:

   ```bash
   curl -i \
     -u "<username>:<password>" \
     http://localhost:8000/api/2/favorites/<username>.json
   ```

2. Confirm the response:
   - returns `200 OK`
   - is a JSON array
   - includes the expected favorite item fields:
     `title`, `url`, `podcast_title`, `podcast_url`, `description`, `website`,
     `released`, and `mygpo_link`

## 5. Validate empty and protected responses

1. Request favorites for a valid user with no favorite rows and confirm the
   response is `[]`.
2. Attempt the request without authentication and confirm the service returns
   `401 Unauthorized`.
3. Attempt to read another user's favorites using different credentials and
   confirm the service returns `403 Forbidden`.
4. Request favorites for an unknown username and confirm the service returns
   `404 Not Found`.

## 6. Run automated verification

1. Install dependencies if needed:

   ```bash
   uv sync
   ```

2. Run repository quality and security checks:

   ```bash
   uv run ruff check .
   uv run mypy app tests
   uv run bandit -r . -c pyproject.toml
   uv run pip-audit
   ```

3. Run the automated test suite:

   ```bash
   uv run pytest -q
   ```

4. Optional favorites-focused shortcut, if added during implementation:

   ```bash
   make verify-favorites
   ```

## 7. Validation Notes

Automated verification for this feature should cover:

- successful authenticated favorite retrieval
- empty favorite responses for valid users
- metadata serialization from episodes and podcast feeds
- cross-account denial and missing-auth rejection
- missing-user `404` behavior
- stable ordering and duplicate-prevention semantics

## 8. Prepare for review

1. Ensure commits follow Conventional Commits.
2. Capture one successful favorites response with populated metadata.
3. Capture one successful empty favorites response.
4. Capture one unauthorized or forbidden favorites response.
5. Capture one missing-user `404` response.

## 9. Implementation Verification Results

Automated checks completed successfully on 2026-04-17:

- `uv run ruff check .`
- `uv run mypy app tests`
- `uv run bandit -r . -c pyproject.toml`
- `uv run pip-audit`
- `uv run pytest -q`
- `uv run pytest -q tests/unit/test_favorite_service.py tests/contract/test_favorites_api.py tests/integration/test_favorites_api_flow.py tests/integration/test_app_startup.py`

Manual-guided endpoint validation was also exercised in a local `TestClient`
session with seeded SQLite data:

- populated favorites request returned `200 OK` with the documented fields
- empty favorites request returned `200 OK` with `[]`
- unauthenticated request returned `401 Unauthorized`
- cross-account request returned `403 Forbidden`
- missing-user request returned `404 Not Found`
