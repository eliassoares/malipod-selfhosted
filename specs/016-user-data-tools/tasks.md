# Tasks: User Data Tools

**Input**: Design documents from `specs/016-user-data-tools/`
**Prerequisites**: `specs/016-user-data-tools/plan.md`, `specs/016-user-data-tools/spec.md`, `specs/016-user-data-tools/contracts/user-data-tools-site.md`, `specs/016-user-data-tools/research.md`

**Tests**: Obrigatórios (NFR-001). Preferir tests em `tests/contract/` e unit tests para merge rules.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos diferentes, sem dependências diretas)
- **[Story]**: Qual user story (ex.: `[US1]`, `[US2]`, `[US3]`, `[US4]`)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Preparar a feature e mapear tabelas cobertas.

- [ ] T001 Confirmar branch `016-user-data-tools` está atualizado com `main` (git)
- [ ] T002 [P] Listar tabelas alvo e regras (chave natural + recência) em `specs/016-user-data-tools/research.md` e validar contra modelos SQLAlchemy

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Criar service e utilitários de snapshot/merge e plumbing no site.

- [ ] T003 Criar service `app/services/user_data_tools.py` com APIs: `export_snapshot(user)`, `import_snapshot(user, payload)`, `delete_user_data(user)`, `delete_user_account(user)`
- [ ] T004 [P] Criar schema(s) Pydantic para validar o JSON exportado/importado em `app/schemas/user_data_tools.py` (formato por tabela; validar tipos básicos e timestamps)
- [ ] T005 Adicionar endpoints (site) em `app/api/routes/profile_site.py`:
  - `POST /user/profile/{nickname}/export`
  - `POST /user/profile/{nickname}/import`
  - `POST /user/profile/{nickname}/delete-data`
  - `POST /user/profile/{nickname}/delete-user`
- [ ] T006 Atualizar UI em `app/templates/profile/detail.html` com 4 botões/forms e confirmação explícita para ações destrutivas

**Checkpoint**: Profile page renderiza os botões e endpoints existem (ainda sem lógica completa).

---

## Phase 3: User Story 1 - Exportar meus dados (Priority: P1) 🎯 MVP

**Goal**: Exportar snapshot JSON por tabela, com filename e sem hashes de senha.

**Independent Test**: Logar, exportar e validar headers/JSON + ausência de `password_hash`/`password_salt` e ausência de `authenticated_sessions`.

### Tests for User Story 1 ⚠️

- [ ] T007 [P] [US1] Criar `tests/contract/test_user_data_tools_site.py` com cenário export (status 200, header `Content-Disposition`, JSON por tabela, sem hashes)
- [ ] T008 [P] [US1] Criar `tests/unit/test_user_data_tools.py` para validar que export remove `password_hash`/`password_salt` e ignora sessões

### Implementation for User Story 1

- [ ] T009 [US1] Implementar export em `app/services/user_data_tools.py` e plugar em `app/api/routes/profile_site.py` (download `malipod_data_YYYY-MM-DD.json`)

---

## Phase 4: User Story 2 - Importar meus dados com segurança (Priority: P2)

**Goal**: Importar JSON exportado e aplicar merge por recência/chave natural.

**Independent Test**: Importar JSON e verificar que registros mais antigos não sobrescrevem os mais recentes, e registros mais novos atualizam.

### Tests for User Story 2 ⚠️

- [ ] T010 [P] [US2] Em `tests/unit/test_user_data_tools.py`, adicionar casos de merge: ignorar quando arquivo é mais antigo; atualizar quando mais novo (por tabela crítica como `devices`, `podcast_feeds`)
- [ ] T011 [P] [US2] Em `tests/contract/test_user_data_tools_site.py`, adicionar cenário import (upload JSON) e validar efeito (ex.: idioma ou setting atualizado conforme recência)
- [ ] T012 [P] [US2] Em `tests/unit/test_user_data_tools.py`, adicionar casos append-only: inserir se não existe e não atualizar eventos existentes

### Implementation for User Story 2

- [ ] T013 [US2] Implementar import + merge em `app/services/user_data_tools.py` seguindo `specs/016-user-data-tools/research.md` (chaves/recência) e garantir isolamento por usuário logado

---

## Phase 5: User Story 3 - Limpar meus dados mantendo a conta (Priority: P3)

**Goal**: Deletar dados associados ao usuário e devices, preservando `users`.

**Independent Test**: Criar dados do usuário, executar delete-data e verificar que `users` persiste e dados associados somem.

### Tests for User Story 3 ⚠️

- [ ] T014 [P] [US3] Em `tests/contract/test_user_data_tools_site.py`, adicionar cenário delete-data (com confirmação), verificando que `users` permanece e alguns dados associados foram removidos

### Implementation for User Story 3

- [ ] T015 [US3] Implementar `delete_user_data` em `app/services/user_data_tools.py` e endpoint `POST /user/profile/{nickname}/delete-data` com confirmação explícita

---

## Phase 6: User Story 4 - Deletar minha conta e sair (Priority: P4)

**Goal**: Deletar usuário e dados, encerrar sessão e redirecionar para `/`.

**Independent Test**: Logar, deletar usuário e verificar redirect + cookie removido e que o usuário não existe mais.

### Tests for User Story 4 ⚠️

- [ ] T016 [P] [US4] Em `tests/contract/test_user_data_tools_site.py`, adicionar cenário delete-user (confirmação), verificando redirect para `/` e que sessão foi encerrada

### Implementation for User Story 4

- [ ] T017 [US4] Implementar `delete_user_account` em `app/services/user_data_tools.py` e endpoint `POST /user/profile/{nickname}/delete-user` (revogar sessão + apagar cookie + redirect `/`)

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Qualidade, validações e evidência de verificação.

- [ ] T018 [P] Rodar `uv run pytest` e registrar evidência no PR
- [ ] T019 [P] Rodar `uv run ruff check .` e corrigir issues sem `# noqa`
- [ ] T020 [P] Validar manualmente `specs/016-user-data-tools/quickstart.md`
- [ ] T021 Preparar descrição do PR com: tabelas cobertas, regras de merge/recência e salvaguardas (segredos, isolamento, confirmação)

---

## Dependencies & Execution Order

- Phase 1 → Phase 2 → US1 → US2 → US3 → US4 → Polish

## Parallel Opportunities

- T002, T004 podem rodar em paralelo.
- T007/T008 (testes export) podem começar antes de T009.
- T010/T012 podem rodar em paralelo (unit tests import).
- T018 e T019 podem rodar em paralelo ao final.

## Suggested MVP Scope

- US1 (export): T007–T009.
