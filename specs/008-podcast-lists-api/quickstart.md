# Quickstart: Podcast Lists API

## Goal

Run the podcast-lists compatibility feature locally, verify public reads and
authenticated CRUD behavior, and confirm generated-name handling before opening
a pull request.

## Prerequisites

- Docker and Docker Compose available locally
- Project dependencies installed with the pinned toolchain
- Existing auth, subscriptions, and episodes flows already working in the repository

## 1. Prepare configuration

1. Ensure your local environment file exists:

   ```bash
   cp .env.example .env
   ```

2. Confirm the application secret and database settings are valid.
3. Create at least one local development account through the existing auth flow.

## 2. Start the application

1. Start the stack:

   ```bash
   docker compose up --build
   ```

2. Wait for PostgreSQL and the FastAPI app to report healthy.
3. Keep one authenticated username and password available for manual checks.

## 3. Create a podcast list

1. Create a list in JSON format:

   ```bash
   curl -i \
     -u "<username>:<password>" \
     -H 'Content-Type: application/json' \
     -X POST \
     "http://localhost:8000/api/2/lists/<username>/create.json?title=My%20Python%20Podcasts" \
     -d '[
       "https://example.com/python.xml",
       "https://example.com/testing.xml"
     ]'
   ```

2. Confirm the response:
   - returns `303 See Other`
   - includes a `Location` header pointing to
     `/api/2/lists/<username>/list/my-python-podcasts.json`
3. Repeat the same request and confirm the service returns `409 Conflict`.

## 4. Read list summaries and one list

1. Fetch the user's list summaries:

   ```bash
   curl -i \
     http://localhost:8000/api/2/lists/<username>.json
   ```

2. Confirm the response includes each list's `title`, `name`, and `web` URL.
3. Fetch one list in JSON:

   ```bash
   curl -i \
     http://localhost:8000/api/2/lists/<username>/list/my-python-podcasts.json
   ```

4. Fetch the same list in OPML and plaintext:

   ```bash
   curl -i \
     http://localhost:8000/api/2/lists/<username>/list/my-python-podcasts.opml

   curl -i \
     http://localhost:8000/api/2/lists/<username>/list/my-python-podcasts.txt
   ```

5. Confirm the same ordered feeds are present across all supported formats.

## 5. Update and delete a list

1. Replace the list content:

   ```bash
   curl -i \
     -u "<username>:<password>" \
     -H 'Content-Type: text/plain' \
     -X PUT \
     http://localhost:8000/api/2/lists/<username>/list/my-python-podcasts.txt \
     --data-binary $'https://example.com/python.xml\nhttps://example.com/async.xml\n'
   ```

2. Confirm the response returns `204 No Content`.
3. Read the list again and confirm the new ordered contents are visible.
4. Delete the list:

   ```bash
   curl -i \
     -u "<username>:<password>" \
     -X DELETE \
     http://localhost:8000/api/2/lists/<username>/list/my-python-podcasts.json
   ```

5. Confirm the response returns `204 No Content`.
6. Read the same list again and confirm the service now returns `404 Not Found`.

## 6. Verify authorization and error behavior

1. Attempt to create, update, or delete a list using another authenticated
   user's credentials and confirm the service rejects the request.
2. Request summaries for an unknown username and confirm the service returns
   `404 Not Found`.
3. Request a missing list name for a known user and confirm the service returns
   `404 Not Found`.
4. Submit an invalid body for the selected format and confirm the service
   returns `400 Bad Request`.

## 7. Run automated verification

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

4. Optional lists-focused shortcut, if added during implementation:

   ```bash
   make verify-lists
   ```

## 8. Validation Notes

Automated verification for this feature should cover:

- canonical-name generation and same-user conflict handling
- list-summary JSON responses and public list reads
- JSON, OPML, and plaintext rendering for individual lists
- authenticated create, update, and delete behavior
- cross-account denial, invalid payload handling, and missing-resource responses

## 9. Prepare for review

1. Ensure commits follow Conventional Commits.
2. Capture one successful create response showing `303 See Other` and the
   generated `Location` header.
3. Capture one list-summary response and one per-list read response.
4. Capture one `409 Conflict` for a duplicate generated name.
5. Capture one forbidden or unauthorized write attempt against another user's
   list.
