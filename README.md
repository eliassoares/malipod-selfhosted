# Malipod

Malipod is the foundation of a podcast synchronization platform inspired by the
gpodder ecosystem. This first increment delivers a single FastAPI application
that exposes both a browser-visible site and a JSON API, with secure startup
validation, pinned dependencies, and isolated verification workflows.

## Stack

- Python 3.13
- FastAPI + Uvicorn
- SQLAlchemy 2.x + asyncpg
- PostgreSQL for development/runtime
- SQLite for automated tests
- Docker Compose for local execution

## Configuration

Copy the example environment file and replace the secret before running the app:

```bash
cp .env.example .env
```

Required settings:

- `APP_NAME`
- `ENVIRONMENT`
- `LOG_LEVEL`
- `ALLOWED_HOSTS`
- `DATABASE_URL`
- `TEST_DATABASE_URL`
- `SECRET_KEY`

The application validates configuration at startup and fails safely if required
values are missing or insecure.

## Run Locally

### Docker Compose

```bash
docker compose up --build
```

Once the stack is ready:

- Site: `http://localhost:8000/`
- API root: `http://localhost:8000/api/v1`
- Liveness: `http://localhost:8000/api/v1/health/live`
- Readiness: `http://localhost:8000/api/v1/health/ready`

### Local process

```bash
uv sync
cp .env.example .env
make run
```

## Verification

Run the full local verification workflow:

```bash
make verify
```

This executes:

- `uv run ruff check .`
- `uv run mypy .`
- `uv run bandit -r . -c pyproject.toml`
- `uv run pip-audit`
- `uv run pytest`

Automated tests use the isolated SQLite context and do not modify the main
PostgreSQL development database.

## Contribution Workflow

- Create a feature branch from `main`
- Use Conventional Commits, for example `feat(api): add readiness endpoint`
- Run `make verify` before review
- Open a pull request with scope, verification evidence, and follow-up items
