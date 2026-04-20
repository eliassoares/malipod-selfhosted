# Tasks: Home Landing Page

**Input**: Design documents from `specs/015-home-landing/`
**Prerequisites**: `specs/015-home-landing/plan.md`, `specs/015-home-landing/spec.md`, `specs/015-home-landing/contracts/home-page.md`

**Tests**: Requeridos (NFR-001). Usar o padrão de `tests/contract/` com `TestClient`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos diferentes, sem dependências diretas)
- **[Story]**: Qual user story (ex.: `[US1]`, `[US2]`, `[US3]`)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Garantir o contexto e referência visual.

- [ ] T001 Confirmar branch `015-home-landing` está atualizado com `main` (git)
- [ ] T002 [P] Revisar referência visual em `google_stitch_templates/landing_page_malipod_next/code.html` e alinhar com `app/templates/base.html`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Garantir que a home recebe contexto consistente com o resto do site.

- [ ] T003 Ajustar `GET /` em `app/api/routes/site.py` para incluir `current_user`, `locale`, `copy`, `page_title`, `app_name`, `supported_locales`
- [ ] T004 [P] Garantir que `app/templates/home.html` estende `app/templates/base.html` e não contém HTML standalone

**Checkpoint**: `/` renderiza usando base/topbar/footer e tem acesso a `current_user` no template.

---

## Phase 3: User Story 1 - Landing page clara para visitantes (Priority: P1) 🎯 MVP

**Goal**: Home explica o Malipod e mostra CTAs de cadastro/login quando deslogado.

**Independent Test**: Acessar `/` sem sessão e validar: contém “Malipod”; mostra CTAs “Cadastro” e “Entrar”; não mostra “Sair”; não contém “gpoddernext”.

### Tests for User Story 1 ⚠️

- [ ] T005 [P] [US1] Criar `tests/contract/test_home_page.py` cobrindo home deslogado (presença de “Malipod”, CTAs de login/cadastro, ausência de “Sair”, ausência de “gpoddernext”)

### Implementation for User Story 1

- [ ] T006 [US1] Reescrever conteúdo de `app/templates/home.html` com texto condizente com Malipod (sync de podcasts + endpoints compatíveis) e CTAs deslogado (`/register`, `/login`)
- [ ] T007 [US1] Garantir que todos textos “gpoddernext/Gpodder Next” foram removidos de `app/templates/home.html`

**Checkpoint**: Home para deslogado está pronta e testável.

---

## Phase 4: User Story 2 - Landing page com ações para usuários logados (Priority: P2)

**Goal**: Home não incentiva login/cadastro quando logado e oferece logout.

**Independent Test**: Acessar `/` com sessão ativa e validar: mostra “Sair” e não mostra CTAs de login/cadastro.

### Tests for User Story 2 ⚠️

- [ ] T008 [P] [US2] Em `tests/contract/test_home_page.py`, adicionar caso logado: mostra “Sair” e não mostra “Cadastro/Entrar”

### Implementation for User Story 2

- [ ] T009 [US2] Em `app/templates/home.html`, condicionar CTAs com Jinja: se `current_user` mostrar form `POST /logout`, senão mostrar links `/register` e `/login`

**Checkpoint**: Home logado vs deslogado correto.

---

## Phase 5: User Story 3 - Experiência mobile-friendly e consistente (Priority: P3)

**Goal**: Layout responsivo e alinhado com o padrão visual do site.

**Independent Test**: Validar manualmente em viewport mobile (sem overflow horizontal).

### Tests for User Story 3

- [ ] T010 [P] [US3] (Opcional) Em `tests/contract/test_home_page.py`, verificar presença de `meta name=\"viewport\"` e ausência de elementos que forcem largura fixa

### Implementation for User Story 3

- [ ] T011 [US3] Ajustar layout responsivo em `app/templates/home.html` (grid/spacing/typography) para telas pequenas
- [ ] T012 [US3] Garantir consistência visual com `partials/topbar.html` e `partials/footer.html` (classes, cores, fontes)

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Qualidade e evidência de verificação.

- [ ] T013 [P] Rodar `uv run pytest` e registrar evidência no PR
- [ ] T014 [P] Rodar `uv run ruff check .` e corrigir issues sem `# noqa`
- [ ] T015 Validar manualmente `specs/015-home-landing/quickstart.md` (home deslogado/logado + viewport mobile)
- [ ] T016 Preparar descrição do PR com: mudanças de copy/layout, comportamento logado vs deslogado, e checklist de verificação

---

## Dependencies & Execution Order

- Phase 1 → Phase 2 → US1 → US2 → US3 → Polish

## Parallel Opportunities

- T002, T004 podem rodar em paralelo.
- T005 pode ser iniciado antes de T006 (TDD).
- T013 e T014 podem rodar em paralelo no final.

## Suggested MVP Scope

- US1: T005–T007 (home deslogado com copy + CTAs e testes).
