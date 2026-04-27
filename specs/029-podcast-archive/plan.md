# Implementation Plan: Podcast Archive

**Branch**: `029-podcast-archive` | **Date**: 2026-04-25 | **Spec**: `specs/029-podcast-archive/spec.md`
**Input**: Feature specification from `specs/029-podcast-archive/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Permitir que o usuário ative “arquivamento” em um podcast, fazendo download de todos os episódios para armazenamento local persistente (via volume) e mantendo o arquivo sincronizado com novos episódios por execução periódica. Ao desativar, cancelar pendentes e remover arquivos baixados com segurança.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.13
**Primary Dependencies**: FastAPI, Starlette, Jinja2Templates, SQLAlchemy 2.x, Alembic, httpx
**Storage**: PostgreSQL (runtime/dev) e SQLite (tests) + filesystem local (volume)
**Testing**: pytest + pytest-asyncio, MyPy strict, Ruff, Bandit, pip-audit
**Target Platform**: Web server + filesystem local persistente em container
**Project Type**: Web app server-rendered + background async worker(s)
**Performance Goals**: Downloads concorrentes limitados; job periódico leve (só enfileirar)
**Constraints**: Sem bloquear requests; evitar path traversal e remoções fora do diretório; idempotência de enfileiramento
**Scale/Scope**: Arquivamento por podcast; status por episódio; sincronização por intervalo fixo

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `Spec-First Delivery`: OK — `specs/029-podcast-archive/spec.md` define histórias, requisitos, critérios e edge cases; este plano e tasks manterão rastreabilidade.
- `Branch Workflow`: OK — branch `029-podcast-archive` criado a partir de `main`.
- `Independently Valuable Slices`: OK — US1 arquiva e baixa (MVP); US2 sincroniza; US3 limpa e cancela.
- `Verification Before Merge`:
  - Automated:
    - `uv run pytest`
    - `uv run ruff check .` + `uv run ruff format .`
    - `uv run mypy app/ tests/`
    - `uv run bandit -r app -c pyproject.toml`
    - `uv run pip-audit` (com política vigente no repo)
  - Manual:
    - Ativar arquivamento e observar status mudando na UI
    - Verificar que o volume `./archive` recebe arquivos e que desativar remove
- `Strict Python Quality Gates`: OK — manter typing estrito e corrigir achados sem suprimir avisos como atalho.
- `Security and Simplicity by Default`:
  - Preferir implementação nativa com asyncio (loop + sleep) para sincronização periódica (evita nova dependência) a menos que o scheduler justificadamente simplifique.
  - Restringir operações de arquivos ao diretório configurado; remover apenas paths conhecidos/relativos gerados pelo sistema.

## Delivery Workflow

- **Base Branch**: `main`
- **Working Branch**: `029-podcast-archive` created from `main`
- **Commit Convention**: Conventional Commits required for every commit
- **Merge Policy**: Open a pull request after implementation and verification are complete

## Project Structure

### Documentation (this feature)

```text
specs/029-podcast-archive/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
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
│   └── routes/
│       └── podcast_archive_site.py    # novo (POST/DELETE archive)
├── core/
│   └── config.py                      # ARCHIVE_DIR, workers, interval
├── db/
│   └── models/
│       ├── podcast.py                 # podcast.archive
│       └── podcast.py                 # episodes.* archive fields (mesmo módulo)
├── services/
│   ├── archive_queue.py               # enqueue/cancel + state transitions
│   ├── archive_worker.py              # download streaming + status updates
│   ├── archive_scheduler.py           # loop periódico para sync
│   └── archive_cleanup.py             # remoção segura de arquivos
└── templates/
    └── podcasts/detail.html           # botões + badges por episódio

alembic/
└── versions/
    └── 0019_podcast_archive.py        # migração (numeração ajustada ao repo)

tests/
├── contract/
├── integration/
└── unit/
```

**Structure Decision**: Feature implementada no layout existente (`app/` + `tests/`) com rotas site para ligar/desligar e serviços assíncronos para fila/worker/scheduler. Persistência no DB + filesystem sob diretório de arquivo configurável.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

Sem violações previstas nesta fase.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| - | - | - |
