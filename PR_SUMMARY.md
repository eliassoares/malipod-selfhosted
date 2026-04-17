# PR Summary

## Scope

- add public `GET /api/2/lists/{username}.json` summary reads and public
  `GET /api/2/lists/{username}/list/{listname}.{format}` list reads in JSON,
  OPML, and plaintext
- add authenticated `POST /api/2/lists/{username}/create.{format}` with
  deterministic canonical-name generation, conflict detection, and `303 See
  Other` redirects
- add authenticated `PUT` and `DELETE`
  `/api/2/lists/{username}/list/{listname}.{format}` for ordered list
  replacement and deletion
- extend the podcast domain with `podcast_lists` and `podcast_list_items`
  persistence while reusing existing `podcast_feeds`

## Verification

- `uv run ruff check .`
- `uv run mypy app tests`
- `uv run bandit -r . -c pyproject.toml`
- `uv run pip-audit`
- `SECRET_KEY=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa DATABASE_URL=sqlite+aiosqlite:///./test.db TEST_DATABASE_URL=sqlite+aiosqlite:///./test.db uv run pytest tests/unit/test_podcast_list_service.py tests/unit/test_subscription_formats.py tests/contract/test_lists_api.py tests/integration/test_lists_api_flow.py tests/integration/test_app_startup.py -q`
- `make verify-lists`

## Migration Notes

- adds `0006_podcast_lists.py`
- creates `podcast_lists` and `podcast_list_items` to support ordered
  user-owned podcast collections linked to existing feed rows

## Deferred Follow-Ups

- list descriptions, visibility flags, or collaborative curation if future
  product scope expands beyond compatibility CRUD
- richer JSON list payloads if clients later need per-entry annotations beyond
  feed URL and lightweight metadata
