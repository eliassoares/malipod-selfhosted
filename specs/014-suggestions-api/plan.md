# Implementation Plan: Suggestions API

**Branch**: `014-suggestions-api` | **Date**: 2026-04-20 | **Spec**: `specs/014-suggestions-api/spec.md`
**Input**: Feature specification from `specs/014-suggestions-api/spec.md`

## Summary

Implementar `GET /suggestions/{number}.{format}` (json|opml|txt), autenticado via
Basic Auth ou cookie de sessão, retornando até `number` podcasts que o usuário
ainda não assina, ordenados por popularidade global (assinantes distintos).

A implementação reutiliza o catálogo local (Directory API / `DirectoryService`)
para obter `subscribers` e metadados, e reutiliza `SubscriptionFormatService`
para renderizar OPML/TXT. O endpoint é read-only e retorna `401` sem autenticação
e `400` para `number` fora de `1..100`.

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: FastAPI, Starlette, Pydantic, SQLAlchemy 2.x
**Storage**: PostgreSQL (runtime/dev), SQLite (tests)
**Testing**: pytest, pytest-asyncio, httpx
**Target Platform**: Linux server (ASGI)
**Project Type**: Web service (gpodder-compatible API)
**Performance Goals**: Responder em < 500ms para até 100 usuários e 500 podcasts distintos (self-hosted).
**Constraints**: Endpoints read-only; sem novas tabelas; sem dependências novas.
**Scale/Scope**: Um único endpoint público (mas autenticado) + testes automatizados.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `Spec-First Delivery`: OK (spec em `specs/014-suggestions-api/spec.md`; este plano; tasks será gerado em `specs/014-suggestions-api/tasks.md`).
- `Branch Workflow`: OK (trabalho no branch `014-suggestions-api`, criado a partir de `main`).
- `Independently Valuable Slices`: OK (P1 JSON é MVP; P2 OPML/TXT incrementais; P3 auth é pré-requisito de P1).
- `Verification Before Merge`: Automatizar casos NFR-001 via testes de API (httpx) + validação manual via curl. Rodar `uv run pytest`, `uv run ruff check .` (e, quando aplicável, `uv run mypy .`, `uv run bandit -r . -c pyproject.toml`).
- `Strict Python Quality Gates`: OK (não usar `# noqa`/`# nosec`; tipagem explícita; evitar exceções não tratadas na camada de rota).
- `Security and Simplicity by Default`: OK (sem novas deps; auth reaproveita `AuthService`; consultas SQLAlchemy com joins e subqueries simples).

## Delivery Workflow

- **Base Branch**: `main`
- **Working Branch**: `014-suggestions-api`
- **Commit Convention**: Conventional Commits (ex.: `feat(suggestions): ...`)
- **Merge Policy**: PR após implementação + verificação; já existe PR draft para artefatos do spec.

## Project Structure

### Documentation (this feature)

```text
specs/014-suggestions-api/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md
```

### Source Code (repository root)

```text
app/
├── api/
│   ├── deps.py
│   └── routes/
│       └── suggestions_api.py
├── services/
│   └── directory.py
└── schemas/
    └── directory.py

tests/
└── api/
    └── test_suggestions_api.py
```

**Structure Decision**: Implementar a rota em `app/api/routes/suggestions_api.py` e a query no `DirectoryService` (para reutilizar o catálogo e a construção de `mygpo_link`), adicionando um helper de autenticação “current user” em `app/api/deps.py` (cookie de sessão ou Basic Auth).

## Complexity Tracking

Nenhuma violação prevista.
