# Contributing to Malipod Selfhosted

Thank you for your interest in contributing!

## Getting started

```bash
git clone https://github.com/eliassoares/malipod-selfhosted.git
cd malipod-selfhosted
uv sync
uv run pre-commit install
uv run pre-commit install --hook-type commit-msg
cp .env.example .env
make run
```

## Running tests

```bash
make test        # full suite (SQLite)
make verify      # lint + typecheck + security + tests
```

## Commit style

This project uses [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(api): add readiness endpoint
fix(auth): handle expired session cookie
docs: update self-hosting guide
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`.

## Pull request checklist

- [ ] `make verify` passes locally
- [ ] New behaviour is covered by tests
- [ ] Commit messages follow Conventional Commits

## Project structure

```
app/
  api/routes/   # FastAPI routers (*_api.py = gpodder API, *_site.py = web UI)
  core/         # Config, localization, security helpers
  db/models/    # SQLAlchemy ORM models
  services/     # Business logic (one class per domain)
  schemas/      # Pydantic schemas
  templates/    # Jinja2 HTML templates
tests/
  unit/         # Pure logic, no DB
  contract/     # HTTP-level API tests (Basic Auth)
  integration/  # Full-flow tests (session cookies + SQLite)
```

## Reporting issues

Use the [issue tracker](https://github.com/eliassoares/malipod-selfhosted/issues).
For security vulnerabilities, see [SECURITY.md](SECURITY.md).
