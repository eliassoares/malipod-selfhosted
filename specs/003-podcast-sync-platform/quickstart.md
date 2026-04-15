# Quickstart: Podcast Sync Platform Foundation

## Goal

Start the initial Malipod foundation locally, verify both the site and API
surfaces, and run the isolated verification workflow before opening a pull
request.

## Prerequisites

- Docker and Docker Compose available locally
- Python toolchain available for local quality checks
- Project dependencies installed through the repository-managed workflow

## 1. Prepare configuration

1. Create the local environment file:

   ```bash
   cp .env.example .env
   ```

2. Review `.env` and provide only development-safe values before startup.
3. Do not reuse production secrets locally.

## 2. Start the platform

1. Build and start the application stack with Docker Compose:

   ```bash
   docker compose up --build
   ```

2. Wait for PostgreSQL and the application service to report healthy.
3. Open [http://localhost:8000/](http://localhost:8000/) in a browser.
4. Call the API endpoints from a second terminal:

   ```bash
   curl http://localhost:8000/api/v1
   curl http://localhost:8000/api/v1/health/live
   curl http://localhost:8000/api/v1/health/ready
   ```

## 3. Verify product surfaces

1. Confirm the home page renders and identifies the platform correctly.
2. Confirm the liveness endpoint responds with HTTP `200`.
3. Confirm the readiness endpoint responds with HTTP `200` and reports check details.
4. Confirm invalid or missing configuration causes safe startup failure with actionable feedback.

## 4. Run isolated verification

1. Install dependencies with the pinned toolchain:

   ```bash
   uv sync
   ```

2. Execute the repository quality and security checks:

   ```bash
   uv run ruff check .
   uv run mypy .
   uv run bandit -r . -c pyproject.toml
   uv run pip-audit
   ```

3. Run the automated test suite against the isolated SQLite test context:

   ```bash
   uv run pytest -q
   ```

4. Confirm the verification flow does not modify the PostgreSQL development data.

## 5. Prepare for review

1. Ensure commits follow Conventional Commits.
2. Collect the executed verification results.
3. Open a pull request using the repository PR template.
4. Summarize implemented scope, verification evidence, and deferred follow-up
   work.
