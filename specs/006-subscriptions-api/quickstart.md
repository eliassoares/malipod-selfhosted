# Quickstart: Subscriptions API

## Goal

Run the subscriptions compatibility feature locally, verify supported read and
write formats, and confirm timestamp-based delta synchronization before opening
a pull request.

## Prerequisites

- Docker and Docker Compose available locally
- Project dependencies installed with the pinned toolchain
- Existing auth and device flows already working in the repository

## 1. Prepare configuration

1. Ensure your local environment file exists:

   ```bash
   cp .env.example .env
   ```

2. Confirm the application secret and database settings are valid.
3. Use a local development account created through the existing auth flows.

## 2. Start the application

1. Start the stack:

   ```bash
   docker compose up --build
   ```

2. Wait for PostgreSQL and the FastAPI app to report healthy.
3. Keep one authenticated username, password, and cookie jar ready for manual
   checks.

## 3. Verify device and account subscription reads

1. Request a device subscription export in JSON:

   ```bash
   curl -i \
     -u "<username>:<password>" \
     http://localhost:8000/subscriptions/<username>/<deviceid>.json
   ```

2. Request the same device in OPML and plaintext:

   ```bash
   curl -i \
     -u "<username>:<password>" \
     http://localhost:8000/subscriptions/<username>/<deviceid>.opml

   curl -i \
     -u "<username>:<password>" \
     http://localhost:8000/subscriptions/<username>/<deviceid>.txt
   ```

3. Request the account-wide union:

   ```bash
   curl -i \
     -u "<username>:<password>" \
     http://localhost:8000/subscriptions/<username>.json
   ```

4. Confirm unsupported formats return `400` and unknown device IDs return `404`
   for device-specific reads.

## 4. Verify full-device upload and auto-created devices

1. Upload plaintext subscriptions for a new device ID:

   ```bash
   printf '%s\n%s\n' \
     "http://example.com/feed.rss" \
     "https://example.org/podcast.xml" \
     | curl -i \
       -u "<username>:<password>" \
       -X PUT \
       --data-binary @- \
       http://localhost:8000/subscriptions/<username>/<new-device>.txt
   ```

2. Confirm the response is `200 OK` with an empty body.
3. Fetch the same device subscriptions and confirm the URLs match the upload.
4. Fetch `/api/2/devices/<username>.json` and confirm the device was created.

## 5. Verify delta upload and delta read behavior

1. Upload a delta payload:

   ```bash
   curl -i \
     -u "<username>:<password>" \
     -H 'Content-Type: application/json' \
     -X POST \
     -d '{"add":["http://example.com/new.xml","ftp://invalid.example/feed"],"remove":["https://example.org/podcast.xml"]}' \
     http://localhost:8000/api/2/subscriptions/<username>/<deviceid>.json
   ```

2. Confirm the response contains:
   - a numeric `timestamp`
   - an `update_urls` pair for any rewritten URL
3. Re-request changes since the prior timestamp:

   ```bash
   curl -i \
     -u "<username>:<password>" \
     "http://localhost:8000/api/2/subscriptions/<username>/<deviceid>.json?since=<timestamp>"
   ```

4. Confirm only newer add/remove changes are returned.
5. Repeat the same delta-read request after no new writes and confirm the
   service returns empty `add` and `remove` lists plus a fresh timestamp.

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

4. Optional subscriptions-focused shortcut, if added during implementation:

   ```bash
   make verify-subscriptions
   ```

## 7. Latest Validation Snapshot

Validated on `2026-04-16` for branch `006-subscriptions-api`.

- `uv run ruff check .` -> All checks passed
- `uv run mypy app tests` -> Success: no issues found in 61 source files
- `uv run bandit -r . -c pyproject.toml` -> No issues identified
- `uv run pip-audit` -> No known vulnerabilities found
- `uv run pytest -q` -> 82 passed
- `make verify-subscriptions` is available as the feature-focused verification shortcut

## 8. Prepare for review

1. Ensure commits follow Conventional Commits.
2. Capture manual evidence for JSON, OPML, and plaintext reads.
3. Capture a successful full upload with an empty body and auto-created device.
4. Capture one delta upload that returns `update_urls` and one delta read with
   an empty change set.
