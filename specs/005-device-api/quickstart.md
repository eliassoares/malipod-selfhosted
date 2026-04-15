# Quickstart: Device API

## Goal

Run the authenticated device contracts locally, verify device registration and
listing behavior, and confirm incremental device update responses work before
opening a pull request.

## Prerequisites

- Docker and Docker Compose available locally
- Project dependencies installed with the pinned toolchain
- A working local database configuration
- At least one existing user account available for authentication

## 1. Prepare the environment

1. Ensure your local environment file exists:

   ```bash
   cp .env.example .env
   ```

2. Confirm the application secret and database settings are present.
3. Use development-only secrets and credentials locally.

## 2. Start the application

1. Start the stack:

   ```bash
   docker compose up --build
   ```

2. Wait for the application and PostgreSQL service to report healthy.
3. Open [http://localhost:8000/](http://localhost:8000/) to confirm the app is up.

## 3. Create or update a device

1. Call the device registration endpoint with HTTP Basic authentication:

   ```bash
   curl -i \
     -u "<nickname>:<password>" \
     -H "Content-Type: application/json" \
     -X POST \
     -d '{"caption":"gPodder on my laptop","type":"laptop"}' \
     http://localhost:8000/api/2/devices/<nickname>/my-laptop.json
   ```

2. Confirm the request succeeds for a valid device ID.
3. Repeat the call with only one field, such as a new caption, and confirm only
   the supplied field changes.
4. Repeat with an invalid device ID such as `bad id` and confirm the request is
   rejected.
5. Repeat the call with credentials for another user and confirm the API denies
   the cross-account update attempt.

## 4. List devices for the account

1. Request the device list:

   ```bash
   curl -i \
     -u "<nickname>:<password>" \
     http://localhost:8000/api/2/devices/<nickname>.json
   ```

2. Confirm the response includes the device ID, caption, type, and subscription
   count for each device.
3. Confirm only the authenticated user's devices are returned.
4. Confirm a user with no registered devices receives `[]`.

## 5. Retrieve incremental device updates

1. Request the initial update snapshot:

   ```bash
   curl -i \
     -u "<nickname>:<password>" \
     "http://localhost:8000/api/2/updates/<nickname>/my-laptop.json"
   ```

2. Record the `timestamp` from the response.
3. Request updates again using the returned timestamp:

   ```bash
   curl -i \
     -u "<nickname>:<password>" \
     "http://localhost:8000/api/2/updates/<nickname>/my-laptop.json?since=<timestamp>"
   ```

4. Confirm the second response returns only newer changes.
5. Repeat with action details enabled:

   ```bash
   curl -i \
     -u "<nickname>:<password>" \
     "http://localhost:8000/api/2/updates/<nickname>/my-laptop.json?include_actions=true"
   ```

6. Confirm updated episodes whose state is not `new` include the latest action
   payload.
7. Confirm an unknown device ID returns `404`.

## 6. Run automated verification

1. Install dependencies:

   ```bash
   uv sync
   ```

2. Run the repository quality and security checks:

   ```bash
   uv run ruff check .
   uv run mypy app tests
   uv run bandit -r . -c pyproject.toml
   uv run pip-audit
   ```

3. Run the full test suite:

   ```bash
   uv run pytest -q
   ```

4. Optional device-focused shortcut during implementation:

   ```bash
   make test-device
   ```

5. Expected focused verification result for this feature branch:

   ```text
   make test-device -> 18 passed
   ```

## 7. Prepare for review

1. Ensure commits follow Conventional Commits.
2. Record manual curl verification for create/update, list, and update retrieval.
3. Record ownership-failure and invalid-device-ID behavior.
4. Record the focused verification result from `make test-device`.
5. Open a pull request summarizing the delivered device contracts, migration
   changes, automated verification, and any deferred sync scope.
