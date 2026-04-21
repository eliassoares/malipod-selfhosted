# Tasks: Subscriptions Page

**Input**: Design documents from `specs/017-subscriptions-page/`
**Prerequisites**: `specs/017-subscriptions-page/plan.md`, `specs/017-subscriptions-page/spec.md`, `specs/017-subscriptions-page/research.md`, `specs/017-subscriptions-page/data-model.md`, `specs/017-subscriptions-page/contracts/`

**Tests**: Incluir testes automatizados (contract/integration/unit) para as rotas SSR, preferências, export OPML e add por URL, além dos quality gates do repo.

**Organization**: Tasks agrupadas por user story para permitir entrega incremental.

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 Confirmar branch e diretório da feature em `specs/017-subscriptions-page/plan.md`
- [x] T002 Registrar baseline de verificação em `specs/017-subscriptions-page/quickstart.md` (rodar servidor e validar rotas)
- [x] T003 [P] Revisar o template de referência em `google_stitch_templates/malipod_minhas_subscricoes/code.html` e extrair componentes reaproveitáveis para `app/templates/subscriptions/index.html`

---

## Phase 2: Foundational (Blocking Prerequisites)

- [x] T004 Criar pasta de assets estáticos em `app/static/placeholders/` e mover `lilith.png` + `malte.png` para essa pasta
- [x] T005 [P] Criar helper de placeholders em `app/core/placeholders.py` (lista de assets e seleção aleatória determinística por chamada)
- [x] T006 [P] Atualizar modelo de feed para default de imagem em `app/db/models/podcast.py` (`PodcastFeedModel.logo_url` com default via `app/core/placeholders.py`)
- [x] T007 Adicionar coluna `episodes.logo_url` em `app/db/models/podcast.py` (`EpisodeModel.logo_url` com default via `app/core/placeholders.py`)
- [x] T008 Criar migração Alembic para `episodes.logo_url` em `alembic/versions/*_add_episodes_logo_url.py` (inclui backfill opcional)
- [x] T009 [P] Adicionar chaves i18n da página em `app/core/localization.py` (en/es/pt-BR) para navegação, títulos, busca, ordenação, views, export e add
- [x] T010 [P] Adicionar constantes de settings keys em `app/core/settings_keys.py` para `subscriptions.view_mode` e `subscriptions.sort`

**Checkpoint**: DB/modelos/strings/base prontos para começar US1.

---

## Phase 3: User Story 1 - Ver minhas subscrições (Priority: P1) 🎯 MVP

**Goal**: Renderizar `/user/subscriptions/{username}` com lista de feeds seguidos e metadados (imagem/placeholder, contagem de episódios, último episódio).

**Independent Test**: Usuário logado acessa a rota e vê lista/estado vazio; deslogado redireciona; mismatch de username dá 404.

### Tests for User Story 1 ⚠️

- [x] T011 [P] [US1] Criar contract tests SSR em `tests/contract/test_subscriptions_page.py` (redirect deslogado, 404 mismatch, 200 logado)
- [x] T012 [P] [US1] Criar fixtures/helpers em `tests/shared/subscriptions_helpers.py` (seed de feeds/episódios/subscrições via `db_session`)

### Implementation for User Story 1

- [x] T013 [P] [US1] Criar DTOs de página em `app/schemas/subscriptions_page.py` (item com title/feed_url/logo_url/episode_count/last_episode_at)
- [x] T014 [US1] Implementar query agregada em `app/services/subscriptions_page.py` (dedupe por feed do usuário, count episódios, max released_at, placeholder fallback)
- [x] T015 [P] [US1] Criar rota SSR em `app/api/routes/subscriptions_site.py` (`GET /user/subscriptions/{username}`) seguindo padrão de `app/api/routes/profile_site.py`
- [x] T016 [US1] Registrar router SSR no app em `app/main.py` (include_router do novo router)
- [x] T017 [P] [US1] Criar template inicial em `app/templates/subscriptions/index.html` (list view, empty state, i18n via `copy[...]`, imagens via `/static/...`)
- [x] T018 [US1] Ajustar topbar (opcional para MVP) para incluir link de subscrições em `app/templates/partials/topbar.html`

**Checkpoint**: US1 completo (SSR renderiza, testes passam).

---

## Phase 4: User Story 2 - Buscar, ordenar e escolher visualização (Priority: P2)

**Goal**: Adicionar busca, ordenação (recent/oldest) e alternância list/grid com preferência persistida.

**Independent Test**: Com múltiplos feeds e episódios, buscar/ordenar altera resultados e o view mode persiste ao recarregar.

### Tests for User Story 2 ⚠️

- [x] T019 [P] [US2] Adicionar testes de ordenação e busca em `tests/contract/test_subscriptions_page.py` (seed com datas diferentes)
- [x] T020 [P] [US2] Adicionar testes de persistência de preferência em `tests/contract/test_subscriptions_page.py` (salvar view mode e garantir que render usa o valor)

### Implementation for User Story 2

- [x] T021 [US2] Implementar parsing de query params (`q`, `sort`, `view`) em `app/api/routes/subscriptions_site.py`
- [x] T022 [US2] Integrar preferences com `SettingsService` em `app/api/routes/subscriptions_site.py` (ler `account_settings` e aplicar defaults)
- [x] T023 [US2] Criar endpoint SSR para salvar preferências em `app/api/routes/subscriptions_site.py` (`POST /user/subscriptions/{username}/preferences` → redirect)
- [x] T024 [US2] Implementar filtro e ordenação na query em `app/services/subscriptions_page.py` (ILIKE, order_by por last_episode_at)
- [x] T025 [US2] Atualizar UI em `app/templates/subscriptions/index.html` (search input GET, select de sort, toggle list/grid POST)

**Checkpoint**: US2 completo (UX de organização pronta e persistente).

---

## Phase 5: User Story 3 - Adicionar podcast por URL (Priority: P3)

**Goal**: Permitir adicionar feed por URL e iniciar processamento assíncrono (subscrição em todos os devices + import/atualização de metadados/episódios).

**Independent Test**: Submeter URL válida cria/ativa subscrição; URL inválida mostra erro; duplicatas não criam itens repetidos.

### Tests for User Story 3 ⚠️

- [x] T026 [P] [US3] Criar contract tests de add por URL em `tests/contract/test_subscriptions_add_url.py` (sucesso, inválida, duplicada)
- [x] T027 [P] [US3] Adicionar unit tests de validação/normalização de URL em `tests/unit/test_placeholders_and_urls.py` (sanitize + bloqueios básicos)

### Implementation for User Story 3

- [x] T028 [US3] Criar service de “subscribe across devices” em `app/services/subscriptions_add.py` (garantir device “web”, aplicar delta para todos os devices do usuário)
- [x] T029 [US3] Criar endpoint SSR de add em `app/api/routes/subscriptions_site.py` (`POST /user/subscriptions/{username}/add`) com validação e feedback (flash no HTML)
- [x] T030 [US3] Atualizar UI de add em `app/templates/subscriptions/index.html` (form de URL, estados de erro/sucesso i18n)
- [x] T031 [US3] Definir e implementar “kickoff” de import em `app/services/feed_import.py` (fetch do feed + parse XML + upsert de `PodcastFeedModel` e `EpisodeModel`)
- [x] T032 [US3] Endurecer segurança de fetch em `app/services/feed_import.py` (bloquear esquemas não-http(s), SSRF básico, timeouts, tamanho máximo)
- [x] T033 [US3] Integrar o kickoff assíncrono ao endpoint em `app/api/routes/subscriptions_site.py` (BackgroundTasks ou mecanismo equivalente)

**Checkpoint**: US3 completo (add funciona e inicia processamento; import básico implementado).

---

## Phase 6: User Story 4 - Exportar minhas subscrições em OPML (Priority: P4)

**Goal**: Exportar feeds seguidos em OPML (download).

**Independent Test**: Download retorna OPML válido com todos os feeds do usuário.

### Tests for User Story 4 ⚠️

- [x] T034 [P] [US4] Criar contract tests de export OPML em `tests/contract/test_subscriptions_export_opml.py` (content-type, attachment, contém feeds)

### Implementation for User Story 4

- [x] T035 [US4] Implementar rota SSR de export em `app/api/routes/subscriptions_site.py` (`GET /user/subscriptions/{username}/export.opml`) reutilizando `app/services/subscription_formats.py`
- [x] T036 [US4] Adicionar link/botão de export na UI em `app/templates/subscriptions/index.html`

**Checkpoint**: US4 completo (export pronto e testado).

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T037 [P] Revisar consistência visual (mobile + desktop) em `app/templates/subscriptions/index.html` e `app/templates/partials/topbar.html`
- [ ] T038 [P] Garantir que todos os textos da página estejam em `app/core/localization.py` (remover strings hardcoded em templates/rotas)
- [ ] T039 Melhorar performance de query em `app/services/subscriptions_page.py` (evitar N+1, índices se necessário via migração em `alembic/versions/`)
- [x] T040 [P] Rodar quality gates e corrigir findings sem suppressions em `pyproject.toml` (ruff/mypy/bandit/pip-audit) e ajustar código afetado
- [ ] T041 [P] Validar o checklist manual em `specs/017-subscriptions-page/quickstart.md` e atualizar se necessário
- [ ] T042 [P] Atualizar resumo do PR em `PR_SUMMARY.md` com escopo, evidências e follow-ups

---

## Dependencies & Execution Order

- Phase 1 → Phase 2 bloqueia todas as stories.
- Após Phase 2:
  - US1 é o MVP e desbloqueia UI/rota principal.
  - US2 depende de US1 (mesma rota/template/service) mas pode ser desenvolvido em paralelo após o esqueleto SSR existir.
  - US3 depende de US1 (página) e Phase 2 (placeholders/modelos), e pode evoluir incrementalmente.
  - US4 depende de US1 (access control + listagem) e reutiliza serviços existentes.

## Parallel Opportunities

- Phase 2: T005, T009, T010 podem rodar em paralelo.
- US1: T011 e T012 podem rodar em paralelo; T013/T015/T017 podem rodar em paralelo.
- US2: T019 e T020 em paralelo; T024 e T025 em paralelo (após ajustes de rota).
- US3: T026 e T027 em paralelo; T031 e T032 em paralelo.
