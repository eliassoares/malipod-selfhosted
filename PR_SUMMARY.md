## Summary

- Deliver the first FastAPI foundation for Malipod with both site and API surfaces
- Add secure runtime configuration validation and readiness checks
- Establish isolated SQLite test execution alongside PostgreSQL development runtime

## Verification

- `uv run ruff check .`
- `uv run mypy .`
- `uv run bandit -r . -c pyproject.toml`
- `uv run pip-audit`
- `uv run pytest -q`

## Follow-Ups

- Add authenticated user accounts and feed subscription entities
- Introduce sync-domain workflows for podcasts and episodes
- Add CI automation once a remote hosting target is configured
