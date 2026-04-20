# Tasks: Suggestions API

**Input**: Design documents from `specs/014-suggestions-api/`
**Prerequisites**: `specs/014-suggestions-api/plan.md`, `specs/014-suggestions-api/spec.md`, `specs/014-suggestions-api/research.md`, `specs/014-suggestions-api/data-model.md`, `specs/014-suggestions-api/contracts/suggestions-api.md`

**Tests**: Requeridos (NFR-001). Preferir testes de contrato em `tests/contract/` seguindo o padrão de `tests/contract/test_directory_api.py`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos diferentes, sem dependências diretas)
- **[Story]**: Qual user story (ex.: `[US1]`, `[US2]`, `[US3]`)
- Cada tarefa inclui path(s) exatos.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Preparar o branch e garantir pré-requisitos do catálogo.

- [x] T001 Confirmar branch `014-suggestions-api` está atualizado com `main` e que `specs/014-suggestions-api/` não está divergente do PR (git)
- [x] T002 Confirmar Directory API (feature 013) está presente no branch base (ver `app/api/routes/directory_api.py`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Infra compartilhada necessária para todos os user stories.

- [x] T003 Implementar dependency `get_required_current_user` em `app/api/deps.py` (cookie de sessão OU Basic Auth; 401 com `WWW-Authenticate: Basic`)
- [x] T004 [P] Adicionar validações utilitárias locais em `app/api/routes/suggestions_api.py` (format/number/erros 400) seguindo padrão de `app/api/routes/directory_api.py`
- [x] T005 Estender `app/services/directory.py` com método de query `suggestions_for_user(user_id: int, limit: int)` (excluir feeds já assinados; ordenar por subscribers desc)

**Checkpoint**: Foundation pronta — US1/US2/US3 podem ser implementadas com consistência.

---

## Phase 3: User Story 1 - Receber sugestões de podcasts não assinados (Priority: P1) 🎯 MVP

**Goal**: Retornar sugestões em JSON com ranking por popularidade global e exclusão de feeds já assinados pelo usuário.

**Independent Test**: Com dois usuários e dois feeds, verificar que o usuário B recebe como sugestão um feed assinado por A e não recebe feeds já assinados por B.

### Tests for User Story 1 ⚠️

- [x] T006 [P] [US1] Criar `tests/contract/test_suggestions_api.py` cobrindo: sugestão aparece para usuário não assinante; exclusão de feeds já assinados; limite `number`
- [x] T007 [P] [US1] Em `tests/contract/test_suggestions_api.py`, adicionar caso “usuário sem assinaturas” retorna `200` com `[]`
- [x] T008 [P] [US1] Em `tests/contract/test_suggestions_api.py`, adicionar caso “servidor com único usuário” retorna `200` com `[]`
- [x] T009 [P] [US1] Em `tests/contract/test_suggestions_api.py`, adicionar caso “`number` fora de 1..100” retorna `400`

### Implementation for User Story 1

- [x] T010 [US1] Criar router `app/api/routes/suggestions_api.py` com `GET /suggestions/{number}.json` autenticado e retornando lista de `PodcastDirectoryItem`
- [x] T011 [US1] Incluir router em `app/main.py` (`app.include_router(suggestions_api_router)`)

**Checkpoint**: `/suggestions/{n}.json` funcionando e com testes de contrato passando.

---

## Phase 4: User Story 2 - Receber sugestões em múltiplos formatos (Priority: P2)

**Goal**: Suportar `opml` e `txt` além de `json`, mantendo o mesmo conjunto e ordem de sugestões.

**Independent Test**: Consultar `/suggestions/5.opml` e `/suggestions/5.txt` e validar que o output contém as URLs esperadas e é parseável.

### Tests for User Story 2 ⚠️

- [x] T012 [P] [US2] Em `tests/contract/test_suggestions_api.py`, adicionar caso OPML: status 200, contém `<opml` e URLs sugeridas
- [x] T013 [P] [US2] Em `tests/contract/test_suggestions_api.py`, adicionar caso TXT: status 200, uma URL por linha
- [x] T014 [P] [US2] Em `tests/contract/test_suggestions_api.py`, adicionar caso format inválido retorna `400`

### Implementation for User Story 2

- [x] T015 [US2] Em `app/api/routes/suggestions_api.py`, adicionar suporte a `GET /suggestions/{number}.{opml|txt}` renderizando via `app/services/subscription_formats.py::SubscriptionFormatService`

**Checkpoint**: OPML/TXT funcionam e testes passam.

---

## Phase 5: User Story 3 - Acesso negado sem autenticação (Priority: P3)

**Goal**: Garantir `401 Unauthorized` sem credenciais válidas.

**Independent Test**: Chamar endpoint sem cookie e sem Basic Auth e confirmar 401 + header `WWW-Authenticate: Basic`.

### Tests for User Story 3 ⚠️

- [x] T016 [P] [US3] Em `tests/contract/test_suggestions_api.py`, adicionar caso sem auth retorna `401` e header `WWW-Authenticate` presente
- [x] T017 [P] [US3] Em `tests/contract/test_suggestions_api.py`, adicionar caso com Basic Auth válido retorna `200`

### Implementation for User Story 3

- [x] T018 [US3] Garantir que `app/api/deps.py#get_required_current_user` retorna `401` com `WWW-Authenticate: Basic` quando não autenticado

**Checkpoint**: comportamento 401 garantido por teste.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Qualidade, documentação e evidência de verificação.

- [x] T019 [P] Rodar `uv run pytest` (incluindo `tests/contract/test_suggestions_api.py`) e registrar resultado no PR
- [x] T020 [P] Rodar `uv run ruff check .` (config em `pyproject.toml`) e corrigir issues sem usar `# noqa`
- [ ] T021 [P] (Se aplicável) Rodar `uv run mypy .` e `uv run bandit -r . -c pyproject.toml` (config em `pyproject.toml`)
- [ ] T022 Validar manualmente comandos de `specs/014-suggestions-api/quickstart.md` (curl Basic Auth)
- [ ] T023 Preparar descrição do PR com referências a `specs/014-suggestions-api/contracts/suggestions-api.md` e evidências de verificação (testes/edge cases)

---

## Dependencies & Execution Order

### Phase Dependencies

- Phase 1 → Phase 2 → (US1, US2, US3) → Polish

### User Story Dependencies

- **US1 (P1)** depende de Phase 2 (auth helper + query de sugestões + rota base)
- **US2 (P2)** depende de US1 (mesmo endpoint + payload), mas pode ser implementada logo após a rota existir
- **US3 (P3)** é garantida principalmente pelo helper de auth (Phase 2), mas tem testes próprios

## Parallel Opportunities

- T006–T009, T012–T014, T016–T017 podem ser feitos em paralelo (mesmo arquivo de testes, mas casos independentes).
- T003 e T005 não devem rodar em paralelo (ambas podem influenciar a assinatura do endpoint).

## Suggested MVP Scope

- Entregar US1 primeiro: `GET /suggestions/{number}.json` + testes (T006–T011).
