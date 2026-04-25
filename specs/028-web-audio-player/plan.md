# Implementation Plan: Web Audio Player Bar

**Branch**: `028-web-audio-player` | **Date**: 2026-04-25 | **Spec**: `specs/028-web-audio-player/spec.md`
**Input**: Feature specification from `specs/028-web-audio-player/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Implementar um player de áudio fixo no rodapé, sempre visível, que mantém o estado do episódio durante navegação (páginas tradicionais) e permite iniciar reprodução a partir de um episódio ou de uma playlist. O player persistirá o último episódio e posição no usuário e registrará eventos de play/pause/conclusão usando as tabelas gpodder existentes por meio de um device web dedicado por usuário.

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: FastAPI, Starlette, Jinja2Templates, SQLAlchemy 2.x, Alembic
**Storage**: PostgreSQL (runtime/dev) e SQLite (tests)
**Testing**: pytest + pytest-asyncio, httpx TestClient, MyPy strict, Ruff, Bandit, pip-audit
**Target Platform**: Web (servidor Python) + browser moderno (HTML5 audio)
**Project Type**: Web app (server-rendered templates + JS vanilla)
**Performance Goals**: UI responsiva; requisições de estado do player leves (JSON pequeno)
**Constraints**: Sem SPA; persistência de fila via sessionStorage; sem PWA/offline
**Scale/Scope**: Feature focada em player web e histórico de reprodução do próprio usuário

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `Spec-First Delivery`: OK — `specs/028-web-audio-player/spec.md` define histórias, requisitos, critérios e edge cases; este plano define artefatos e verificação.
- `Branch Workflow`: OK — branch `028-web-audio-player` criado a partir de `main`.
- `Independently Valuable Slices`: OK — US1 entrega player persistente e controles; US2 adiciona fila; US3 adiciona retomada + histórico.
- `Verification Before Merge`:
  - Automated:
    - `uv run pytest` (inclui testes unit/integration novos)
    - `uv run ruff check .` + `uv run ruff format .`
    - `uv run mypy app/ tests/`
    - `uv run bandit -r app -c pyproject.toml`
    - `uv run pip-audit` (com a política atual do repo)
  - Manual:
    - Validar navegação entre páginas mantendo player (quickstart)
    - Validar avanço automático da fila (playlist e podcast)
    - Validar que usuário sem estado anterior inicia com player inativo
- `Strict Python Quality Gates`: OK — novos módulos terão typing estrito; sem `# noqa`/`# nosec`.
- `Security and Simplicity by Default`:
  - Sem dependências novas; player é JS vanilla.
  - Novos endpoints `/web/*` autenticados via sessão; owner-only por definição (estado sempre no usuário da sessão).

## Delivery Workflow

- **Base Branch**: `main`
- **Working Branch**: `028-web-audio-player` created from `main`
- **Commit Convention**: Conventional Commits required for every commit
- **Merge Policy**: Open a pull request after implementation and verification are complete

## Project Structure

### Documentation (this feature)

```text
specs/028-web-audio-player/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
```text
app/
├── api/
│   ├── deps.py
│   └── routes/
│       ├── episode_site.py
│       ├── episode_playlists_site.py
│       └── web_player_api.py          # novo
├── core/
│   └── localization.py                # novas chaves (copy)
├── db/
│   └── models/
│       ├── user.py                    # novas colunas last_*
│       └── podcast.py                 # playlists (posição opcional)
├── services/
│   ├── episodes.py                    # reuso para inserir ações gpodder
│   └── web_player.py                  # novo
├── static/
│   └── js/
│       └── player.js                  # novo
└── templates/
    ├── base.html                      # inclui barra e injeção do estado
    ├── episodes/detail.html           # botão Play
    ├── playlists/detail.html          # botão Play Playlist
    └── partials/player_bar.html       # novo

tests/
├── integration/                       # presença do player + rotas web
└── unit/                              # web player service + device idempotente
```

**Structure Decision**: Implementação como web app server-rendered existente: FastAPI + Jinja2 templates, com um único arquivo JS em `app/static/js/player.js` e rotas JSON novas sob `app/api/routes/web_player_api.py`. Persistência via SQLAlchemy/Alembic em `users` e (opcionalmente) em itens de playlist para ordenação.

## Complexity Tracking

Sem violações previstas nesta fase.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| - | - | - |
