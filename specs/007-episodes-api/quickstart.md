# Quickstart: Episodes API

## Goal

Run the episode-actions compatibility feature locally, verify upload and
retrieval behavior, and confirm timestamp-based incremental synchronization
before opening a pull request.

## Prerequisites

- Docker and Docker Compose available locally
- Project dependencies installed with the pinned toolchain
- Existing auth, device, and subscriptions flows already working in the repository

## 1. Prepare configuration

1. Ensure your local environment file exists:

   ```bash
   cp .env.example .env
   ```

2. Confirm the application secret and database settings are valid.
3. Create a local development account through the existing auth flow.

## 2. Start the application

1. Start the stack:

   ```bash
   docker compose up --build
   ```

2. Wait for PostgreSQL and the FastAPI app to report healthy.
3. Keep one authenticated username and password available for manual checks.

## 3. Verify upload of episode actions

1. Upload a mixed action batch:

   ```bash
   curl -i \
     -u "<username>:<password>" \
     -H 'Content-Type: application/json' \
     -X POST \
     -d '[
       {
         "podcast": "https://example.com/feed.xml",
         "episode": "https://example.com/episode-1.mp3",
         "device": "gpodder_laptop",
         "action": "download",
         "timestamp": "2026-04-16T09:00:00Z"
       },
       {
         "podcast": "https://example.com/feed.xml",
         "episode": "https://example.com/episode-1.mp3",
         "action": "play",
         "started": 15,
         "position": 120,
         "total": 500
       }
     ]' \
     http://localhost:8000/api/2/episodes/<username>.json
   ```

2. Confirm the response contains:
   - a numeric `timestamp`
   - an `update_urls` list, empty or populated depending on sanitation
3. Repeat with an invalid URL such as `ftp://invalid.example/episode.ogg` and
   confirm the response reports a rewritten pair with an empty-string target.
4. Repeat with an incomplete `play` action missing one progress field and
   confirm the service rejects the request.

## 4. Verify retrieval of episode actions

1. Retrieve all stored actions:

   ```bash
   curl -i \
     -u "<username>:<password>" \
     http://localhost:8000/api/2/episodes/<username>.json
   ```

2. Confirm the response includes an `actions` array and a fresh `timestamp`.
3. Upload another action and retrieve with the prior timestamp:

   ```bash
   curl -i \
     -u "<username>:<password>" \
     "http://localhost:8000/api/2/episodes/<username>.json?since=<timestamp>"
   ```

4. Confirm only newer uploads are returned.
5. Repeat the same retrieval after no further uploads and confirm the response
   returns an empty `actions` array plus a fresh timestamp.

## 5. Verify filters and aggregation

1. Filter by podcast:

   ```bash
   curl -i \
     -u "<username>:<password>" \
     "http://localhost:8000/api/2/episodes/<username>.json?podcast=https://example.com/feed.xml"
   ```

2. Filter by device:

   ```bash
   curl -i \
     -u "<username>:<password>" \
     "http://localhost:8000/api/2/episodes/<username>.json?device=gpodder_laptop"
   ```

3. Enable aggregation:

   ```bash
   curl -i \
     -u "<username>:<password>" \
     "http://localhost:8000/api/2/episodes/<username>.json?aggregated=true"
   ```

4. Confirm podcast and device filters limit the result set correctly.
5. Confirm `aggregated=true` returns only the latest action per episode in the
   matching result set.

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

4. Optional episodes-focused shortcut, if added during implementation:

   ```bash
   make verify-episodes
   ```

## 7. Validation Notes

Automated verification completed for this feature during implementation with:

```bash
uv run ruff check app tests
uv run mypy app tests
SECRET_KEY=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa DATABASE_URL=sqlite+aiosqlite:///./test.db TEST_DATABASE_URL=sqlite+aiosqlite:///./test.db uv run pytest tests/unit/test_episode_service.py tests/contract/test_episodes_api.py tests/integration/test_episodes_sync_api.py tests/unit/test_device_service.py tests/integration/test_device_updates_api.py -q
make verify-episodes
```

The automated coverage validates:

- mixed upload batches and invalid `play` payload rejection
- URL sanitation and `update_urls` reporting
- initial and incremental retrieval via `since`
- filtering by `podcast` and `device`
- `aggregated=true` latest-action behavior
- compatibility with `/api/2/updates/{username}/{deviceid}.json`

## 8. Prepare for review

1. Ensure commits follow Conventional Commits.
2. Capture a successful mixed-action upload with a returned `timestamp`.
3. Capture one retrieval using `since` and one retrieval using `aggregated=true`.
4. Capture one validation failure for an incomplete `play` action and one
   `update_urls` result for a sanitized invalid URL.
