# Implementation Plan: Subscriptions Page

**Branch**: `017-subscriptions-page` | **Date**: 2026-04-21 | **Spec**: `specs/017-subscriptions-page/spec.md`
**Input**: Feature specification from `specs/017-subscriptions-page/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Criar uma página HTML “Minhas subscrições” em `GET /user/subscriptions/{username}`
integrada ao layout existente (`app/templates/base.html` + partials), multilíngue e
mobile-friendly, para o usuário:

- ver os podcasts que segue (imagem/placeholder, nome, contagem de episódios e data/tempo do último episódio)
- pesquisar e ordenar (mais recentes / mais antigos, baseado no último episódio)
- alternar entre lista e grid com preferência persistida
- exportar em OPML
- adicionar podcast por URL (disparando processamento assíncrono para validar URL, adicionar em todos os devices do usuário e importar episódios/metadados)

Além disso, definir estratégia de placeholders de imagem:

- mover `lilith.png` e `malte.png` para uma pasta de assets estáticos apropriada
- definir `podcast_feeds.logo_url` com valor padrão (placeholder aleatório quando ausente)
- adicionar `episodes.logo_url` com valor padrão (placeholder aleatório quando ausente)

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.13
**Primary Dependencies**: FastAPI, Starlette, Jinja2Templates, SQLAlchemy 2.x, Alembic, Tailwind CDN (sem build step)
**Storage**: PostgreSQL (runtime/dev), SQLite (tests)
**Testing**: pytest, pytest-asyncio, httpx (TestClient), contract + integration + unit tests
**Target Platform**: ASGI server (Uvicorn)
**Project Type**: Web service com páginas HTML (SSR) + APIs JSON (gpodder compat)
**Performance Goals**:
- renderização server-side rápida (listagem + agregações básicas)
- busca/ordenação “instantânea” (<= 1s percebido) até ~1.000 subscrições
**Constraints**:
- seguir o padrão visual das páginas existentes (`base.html`, `partials/topbar.html`, `partials/footer.html`)
- multilíngue via `app/core/localization.py` (strings via `copy[...]`)
- assets estáticos servidos por `app/static/` (sem pipeline extra)
- sem novas dependências de job runner no MVP, a não ser que justificado no research
**Scale/Scope**:
- novas rotas HTML e possivelmente endpoints internos (export OPML, salvar preferências)
- queries agregadas para contagem de episódios e último episódio por podcast
- migração DB para `episodes.logo_url` e defaults de placeholder

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `Spec-First Delivery`: OK (`specs/017-subscriptions-page/spec.md`, este plano; tasks em seguida).
- `Branch Workflow`: OK (branch `017-subscriptions-page` criado a partir de `main`).
- `Independently Valuable Slices`: OK (P1: visualizar; P2: buscar/ordenar/view mode; P3: adicionar por URL; P4: OPML).
- `Verification Before Merge`:
  - Automatizado (contrato/integration): `/user/subscriptions/{nickname}` (logado vs deslogado), busca/ordenação, persistência da view (via settings), export OPML, validação de URL para add.
  - Checks: `uv run pytest`, `uv run ruff check .`, `uv run mypy .`, `uv run bandit -r . -c pyproject.toml`, `uv run pip-audit`
  - Manual: viewport mobile (sem overflow), grid/list visual, estados (vazio/erro/loading) e i18n (pt-BR/en/es) sem strings “soltas”.
- `Strict Python Quality Gates`: OK (tipagem strict + ruff security; sem `# noqa`/`# nosec` como atalho).
- `Security and Simplicity by Default`:
  - Preferência por persistência via `account_settings` (já existente), evitando novo storage.
  - Para “add por URL”, validar/sanitizar input e limitar acesso a rede no worker (planejar segurança).

## Delivery Workflow

- **Base Branch**: `main`
- **Working Branch**: `017-subscriptions-page`
- **Commit Convention**: Conventional Commits
- **Merge Policy**: Open a pull request after implementation and verification are complete

## Project Structure

### Documentation (this feature)

```text
specs/017-subscriptions-page/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
app/
├── api/
│   ├── deps.py
│   └── routes/
│       ├── subscriptions_api.py
│       ├── profile_site.py
│       └── subscriptions_site.py        # novo (SSR: /user/subscriptions/{username})
├── core/
│   └── localization.py                  # novas chaves de copy (i18n)
├── db/
│   ├── models/
│   │   └── podcast.py                   # episodes.logo_url + defaults de placeholder
│   └── ...
├── services/
│   ├── subscriptions.py                 # já existe (API)
│   ├── settings.py                      # já existe (persistir view mode/sort)
│   └── subscriptions_page.py            # novo (queries/DTOs para a página)
├── static/
│   └── placeholders/
│       ├── lilith.png
│       └── malte.png
└── templates/
    ├── base.html
    ├── partials/
    └── subscriptions/
        └── index.html                   # novo template

alembic/
└── versions/
    └── *_add_episode_logo_url*.py       # nova migration

tests/
├── contract/
│   ├── test_subscriptions_page.py       # novo (SSR)
│   └── test_subscriptions_export.py     # novo (OPML)
└── integration/
    └── test_subscriptions_add_url.py    # novo (form + background kickoff)
```

**Structure Decision**:
- Criar rota SSR em `app/api/routes/subscriptions_site.py` seguindo o padrão de `app/api/routes/profile_site.py` (redirect para login, 404 se nickname não é do usuário).
- Introduzir um service dedicado `app/services/subscriptions_page.py` para encapsular:
  - query de subscrições do usuário (dedupe por feed)
  - agregações (count episódios + max released_at)
  - filtros (search) e ordenação
- Persistir preferências de UI em `account_settings.settings` via `SettingsService` (sem novo storage).
- Reimplementar o design do template de referência (`google_stitch_templates/malipod_minhas_subscricoes/code.html`) dentro do padrão do site (topbar/footer), evitando dependências extras.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

Nenhuma violação prevista neste momento.
