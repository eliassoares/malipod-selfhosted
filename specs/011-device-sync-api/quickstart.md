# Quickstart: Device Synchronization API

## Goal

Run the device synchronization compatibility feature locally, verify the status
payload shape, validate start/stop synchronization semantics, and confirm access
control before opening a pull request.

## Prerequisites

- Docker and Docker Compose available locally
- Project dependencies installed with the pinned toolchain
- Device API (`/api/2/devices/...`) and Auth API (`/api/2/auth/...`) already
  working in the repository

## 1. Prepare configuration

1. Ensure your local environment file exists:

   ```bash
   cp .env.example .env
   ```

2. Confirm the application secret and database settings are valid.

## 2. Start the application

```bash
docker compose up --build
```

Wait for PostgreSQL and the FastAPI app to report healthy.

## 3. Create a user and register a few devices

1. Create an account using the existing website flow or registration endpoint.
2. Register a few devices for the same user:

   ```bash
   curl -i \
     -u "<username>:<password>" \
     -H "Content-Type: application/json" \
     -d '{"caption":"My Notebook","type":"laptop"}' \
     http://localhost:8000/api/2/devices/<username>/notebook.json
   ```

   Repeat for `netbook`, `pc-work`, etc.

## 4. Read sync status (GET)

```bash
curl -i \
  -u "<username>:<password>" \
  http://localhost:8000/api/2/sync-devices/<username>.json
```

Confirm:

- `200 OK`
- response is a JSON object with keys `synchronized` and `not-synchronized`
- when no groups exist, `synchronized` is `[]` and `not-synchronized` lists all devices

## 5. Start synchronization (POST)

Synchronize two devices into the same group:

```bash
curl -i \
  -u "<username>:<password>" \
  -H "Content-Type: application/json" \
  -d '{"synchronize":[["notebook","netbook"]]}' \
  http://localhost:8000/api/2/sync-devices/<username>.json
```

Confirm the response status shows a group containing both device IDs.

## 6. Stop synchronization (POST)

Remove a device from its group:

```bash
curl -i \
  -u "<username>:<password>" \
  -H "Content-Type: application/json" \
  -d '{"stop-synchronize":["netbook"]}' \
  http://localhost:8000/api/2/sync-devices/<username>.json
```

Confirm `netbook` appears under `not-synchronized`. If the remaining group drops
below 2 devices, confirm it disappears from `synchronized`.

## 7. Validate protected responses

1. Call the endpoint without authentication and confirm it returns `401 Unauthorized`.
2. Call the endpoint with credentials for a different user and confirm it returns `403 Forbidden`.
3. Call POST referencing a missing device ID and confirm it returns `400 Bad Request` with no partial changes.

## 8. Run automated verification

```bash
uv sync
uv run ruff check .
uv run mypy app tests
uv run bandit -r . -c pyproject.toml
uv run pip-audit
uv run pytest -q
```

## 9. Prepare for review

- Ensure commits follow Conventional Commits.
- Capture one successful GET response (no groups).
- Capture one successful POST response (after grouping).
- Capture one successful POST response (after stop-sync).
- Capture one cross-account denial response.
