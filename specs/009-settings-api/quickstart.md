# Quickstart: Settings API

## Goal

Run the settings compatibility feature locally, verify authenticated reads and
writes across all four scopes, and confirm scope-specific validation before
opening a pull request.

## Prerequisites

- Docker and Docker Compose available locally
- Project dependencies installed with the pinned toolchain
- Existing auth, device, subscription, and episode flows already working in the repository
- At least one development user plus one device, podcast feed, and episode
  already present for manual scope checks beyond account scope

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

## 3. Save and read account settings

1. Save account-scoped settings:

   ```bash
   curl -i \
     -u "<username>:<password>" \
     -H 'Content-Type: application/json' \
     -X POST \
     http://localhost:8000/api/2/settings/<username>/account.json \
     -d '{
       "set": {
         "public_profile": false,
         "store_user_agent": true,
         "custom_account_flag": {"level": 2}
       },
       "remove": []
     }'
   ```

2. Confirm the response returns `200 OK` and includes the stored keys.
3. Read the same account settings:

   ```bash
   curl -i \
     -u "<username>:<password>" \
     http://localhost:8000/api/2/settings/<username>/account.json
   ```

4. Confirm the response body matches the saved JSON object.

## 4. Save and read device settings

1. Save settings for an existing device:

   ```bash
   curl -i \
     -u "<username>:<password>" \
     -H 'Content-Type: application/json' \
     -X POST \
     "http://localhost:8000/api/2/settings/<username>/device.json?device=phone" \
     -d '{
       "set": {
         "playback_speed": 1.25,
         "queue_mode": "newest-first"
       },
       "remove": []
     }'
   ```

2. Confirm the response returns `200 OK`.
3. Read the device settings:

   ```bash
   curl -i \
     -u "<username>:<password>" \
     "http://localhost:8000/api/2/settings/<username>/device.json?device=phone"
   ```

4. Confirm the response contains only that device scope's settings.

## 5. Save and read podcast settings

1. Save settings for an existing podcast feed:

   ```bash
   curl -i \
     -u "<username>:<password>" \
     -H 'Content-Type: application/json' \
     -X POST \
     "http://localhost:8000/api/2/settings/<username>/podcast.json?podcast=https://example.com/feed.xml" \
     -d '{
       "set": {
         "public_subscription": false,
         "sync_window_days": 14
       },
       "remove": []
     }'
   ```

2. Confirm the response returns `200 OK`.
3. Read the same podcast settings:

   ```bash
   curl -i \
     -u "<username>:<password>" \
     "http://localhost:8000/api/2/settings/<username>/podcast.json?podcast=https://example.com/feed.xml"
   ```

## 6. Save and read episode settings

1. Save settings for an existing episode:

   ```bash
   curl -i \
     -u "<username>:<password>" \
     -H 'Content-Type: application/json' \
     -X POST \
     "http://localhost:8000/api/2/settings/<username>/episode.json?podcast=https://example.com/feed.xml&episode=https://example.com/episodes/1.mp3" \
     -d '{
       "set": {
         "is_favorite": true,
         "bookmark": {"position": 123}
       },
       "remove": []
     }'
   ```

2. Confirm the response returns `200 OK`.
3. Read the episode settings:

   ```bash
   curl -i \
     -u "<username>:<password>" \
     "http://localhost:8000/api/2/settings/<username>/episode.json?podcast=https://example.com/feed.xml&episode=https://example.com/episodes/1.mp3"
   ```

4. Confirm nested JSON values round-trip unchanged.

## 7. Verify removal and validation behavior

1. Remove one key from account scope:

   ```bash
   curl -i \
     -u "<username>:<password>" \
     -H 'Content-Type: application/json' \
     -X POST \
     http://localhost:8000/api/2/settings/<username>/account.json \
     -d '{
       "set": {},
       "remove": ["custom_account_flag"]
     }'
   ```

2. Confirm the removed key is absent from the response.
3. Omit the required `device` query parameter for device scope and confirm the
   API returns `400 Bad Request`.
4. Attempt a write with another user's credentials and confirm the API returns
   `403 Forbidden`.
5. Request a missing device, podcast, or episode target and confirm the API
   returns `404 Not Found`.

## 8. Run automated verification

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

4. Optional settings-focused shortcut, if added during implementation:

   ```bash
   make verify-settings
   ```

## 9. Validation Notes

Automated verification for this feature should cover:

- authenticated account, device, podcast, and episode reads
- authenticated writes with `set` and `remove`
- empty valid scopes returning `{}` when no settings document exists yet
- malformed payload rejection
- missing required query parameter rejection
- nested JSON round-tripping without type loss
- cross-account denial and missing-target `404` behavior

## 10. Prepare for review

1. Ensure commits follow Conventional Commits.
2. Capture one successful account-scope write response.
3. Capture one successful device, podcast, and episode read response.
4. Capture one invalid-scope or missing-parameter `400` response.
5. Capture one cross-account denial response.
