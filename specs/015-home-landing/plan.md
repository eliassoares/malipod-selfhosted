# Implementation Plan: Home Landing Page

**Branch**: `015-home-landing` | **Date**: 2026-04-20 | **Spec**: `specs/015-home-landing/spec.md`
**Input**: Feature specification from `specs/015-home-landing/spec.md`

## Summary

Substituir a página inicial (`GET /`) por uma landing page moderna e mobile-friendly
para o Malipod, inspirada no layout em `google_stitch_templates/landing_page_malipod_next/`,
mas implementada dentro do padrão visual existente do site (`app/templates/base.html`
e partials).

A página deve:
- trocar toda menção a “gpoddernext/Gpodder Next” por “Malipod”
- explicar o que o Malipod faz (sync de podcasts + APIs compatíveis com gpodder)
- exibir CTAs coerentes com o estado de autenticação:
  - deslogado: mostrar “Criar conta” e “Entrar”; não mostrar “Sair”
  - logado: mostrar “Sair”; não mostrar “Criar conta/Entrar”

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: FastAPI, Starlette, Jinja2Templates, Tailwind CDN config (no build step)
**Storage**: PostgreSQL (runtime/dev), SQLite (tests) — *não há mudança de storage*
**Testing**: pytest + fastapi TestClient (contract/integration)
**Target Platform**: ASGI server
**Project Type**: Web service com páginas HTML + API JSON
**Performance Goals**: renderização server-side rápida (1 página, sem queries extras)
**Constraints**:
- Reutilizar layout existente (base/topbar/footer/head)
- Reutilizar auth por cookie de sessão (já existente) para detectar `current_user`
- Não introduzir novos assets obrigatórios nem pipeline de frontend
**Scale/Scope**: atualizar `app/templates/home.html` e o handler `GET /` para passar o contexto necessário.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `Spec-First Delivery`: OK (`specs/015-home-landing/spec.md`, este plano, tasks em seguida).
- `Branch Workflow`: OK (branch `015-home-landing` criado a partir de `main`).
- `Independently Valuable Slices`: OK (P1: visitantes; P2: logados; P3: mobile/consistência).
- `Verification Before Merge`:
  - Automatizado: testes para `/` deslogado e logado (CTAs corretos + ausência de “gpoddernext”).
  - Checks: `uv run pytest`, `uv run ruff check .`
  - Manual: validar viewport mobile (sem overflow) e navegação no topbar.
- `Strict Python Quality Gates`: OK (sem suppressions; tipagem consistente).
- `Security and Simplicity by Default`: OK (apenas apresentação; sem novas deps; sem alterações no fluxo de auth).

## Delivery Workflow

- **Base Branch**: `main`
- **Working Branch**: `015-home-landing`
- **Commit Convention**: Conventional Commits
- **Merge Policy**: PR após implementação + verificação

## Project Structure

### Documentation (this feature)

```text
specs/015-home-landing/
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
├── api/routes/site.py
├── api/routes/auth_site.py
└── templates/
    ├── base.html
    ├── home.html
    └── partials/
        ├── head.html
        ├── topbar.html
        └── footer.html

tests/
└── contract/
    └── test_home_page.py
```

**Structure Decision**:
- Atualizar `app/api/routes/site.py` para incluir `current_user`, `locale`, `copy` e `supported_locales` no contexto do template (mesmo padrão usado em `app/api/routes/auth_site.py`).
- Reescrever `app/templates/home.html` para estender `base.html` e renderizar hero/sections com Tailwind + partials existentes, usando condicionais Jinja para CTAs conforme `current_user`.

## Complexity Tracking

Nenhuma violação prevista.
