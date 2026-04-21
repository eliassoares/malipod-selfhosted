# Implementation Plan: User Data Tools

**Branch**: `016-user-data-tools` | **Date**: 2026-04-20 | **Spec**: `specs/016-user-data-tools/spec.md`
**Input**: Feature specification from `specs/016-user-data-tools/spec.md`

## Summary

Adicionar quatro ações na página de perfil do usuário logado:
- **Exportar dados**: baixar um snapshot JSON (`malipod_data_{DATA}.json`) com um campo por tabela relevante, incluindo `users` (sem `password_hash`/`password_salt`) e excluindo sessões efêmeras.
- **Importar dados**: aceitar o JSON exportado e aplicar merge por tabela usando chaves naturais e coluna de recência (não sobrescrever dados mais novos).
- **Deletar dados**: remover dados do usuário em todas as tabelas com `user_id` (exceto `users`) e dados associados a devices do usuário (`device_pk`).
- **Deletar usuário**: remover tudo (incluindo `users`), deslogar e redirecionar para `/`.

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: FastAPI, Starlette, Jinja2Templates, SQLAlchemy 2.x
**Storage**: PostgreSQL (runtime/dev), SQLite (tests)
**Testing**: pytest, pytest-asyncio, FastAPI TestClient/httpx
**Target Platform**: ASGI server
**Project Type**: Web service (HTML pages + JSON APIs)
**Performance Goals**: export/import em tempo razoável para contas típicas (self-hosted)
**Constraints**:
- Sem novas dependências
- Operações somente para usuário autenticado e apenas no seu próprio escopo
- Sem export/import de segredos (hash/salt) nem sessões efêmeras
- Operações destrutivas com confirmação explícita
**Scale/Scope**: novos handlers no site profile + novo service para snapshot/export/import/cleanup.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `Spec-First Delivery`: OK (`specs/016-user-data-tools/spec.md`, este plano, tasks em seguida).
- `Branch Workflow`: OK (`016-user-data-tools` criado a partir de `main`).
- `Independently Valuable Slices`: OK (P1 export é útil sozinho; P2 import adiciona restore; P3/P4 destrutivos separados).
- `Verification Before Merge`:
  - Testes automatizados para: visibilidade dos botões (somente logado), export sem hashes, import merge por recência, delete-data preserva `users`, delete-user remove `users` + redirect `/` + logout.
  - Rodar `uv run pytest` e `uv run ruff check .`.
- `Strict Python Quality Gates`: OK (sem `# noqa`/`# nosec`; corrigir raiz).
- `Security and Simplicity by Default`: OK (reutilizar `get_current_user` e sessão; importar restrito ao usuário atual; sem dependências).

## Delivery Workflow

- **Base Branch**: `main`
- **Working Branch**: `016-user-data-tools`
- **Commit Convention**: Conventional Commits
- **Merge Policy**: PR após implementação + verificação

## Project Structure

### Documentation (this feature)

```text
specs/016-user-data-tools/
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
│   └── routes/
│       └── profile_site.py
├── services/
│   └── user_data_tools.py
└── templates/
    └── profile/
        └── detail.html

tests/
├── contract/
│   └── test_user_data_tools_site.py
└── unit/
    └── test_user_data_tools.py
```

**Structure Decision**:
- UI via `app/templates/profile/detail.html` (4 novos botões/forms).
- Endpoints (site) em `app/api/routes/profile_site.py` protegidos por sessão (redirect para `/login` se não autenticado).
- Core logic em `app/services/user_data_tools.py` para export/import/delete com transações.

## Complexity Tracking

Nenhuma violação prevista.
