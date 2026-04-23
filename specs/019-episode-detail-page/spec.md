# Feature Specification: Episode Detail Page

**Feature Branch**: `019-episode-detail-page`
**Created**: 2026-04-22
**Status**: Draft
**Input**: User description: "Implementar a página de detalhe do episódio (template: `google_stitch_templates/malipod_detalhe_do_episodio`) com progresso, download, detalhes do episódio, histórico de ouvidas (se possível), favoritar e compartilhar. A página será acessada a partir da listagem de episódios na página do podcast."

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.

  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Ver detalhe do episódio (Priority: P1)

Como usuário autenticado, eu quero abrir uma página de detalhe de um episódio, para ver suas informações completas e o meu progresso.

**Why this priority**: É o núcleo do recurso e habilita o usuário a entender rapidamente onde parou e o contexto do episódio.

**Independent Test**: Pode ser testado acessando a página de um episódio existente e validando que metadata, imagem (ou placeholder) e progresso aparecem, incluindo estado de “não encontrado”.

**Acceptance Scenarios**:

1. **Given** que estou autenticado e o episódio existe, **When** eu abro a página de detalhe, **Then** eu vejo título, descrição (quando existir), data de lançamento, imagem (ou placeholder), tempo total (quando existir) e tempo assistido/escutado (quando existir), além de um indicador visual de progresso.
2. **Given** que estou autenticado e o episódio não existe, **When** eu abro a página, **Then** eu recebo um 404 com mensagem amigável.
3. **Given** que o episódio não tem imagem, **When** eu abro a página, **Then** a UI exibe um placeholder sem quebrar o layout.

---

### User Story 2 - Baixar e compartilhar episódio (Priority: P2)

Como usuário, eu quero poder baixar e compartilhar o episódio, para consumir offline e enviar o link para outras pessoas.

**Why this priority**: São ações comuns e de alto valor, mas a página já é útil sem elas.

**Independent Test**: Pode ser testado verificando que a ação de download aparece quando existe um link baixável e que o compartilhamento fornece um link válido para o episódio.

**Acceptance Scenarios**:

1. **Given** que o episódio possui uma URL de mídia baixável, **When** eu clico em “baixar”, **Then** o download é iniciado (ou o navegador inicia o download) sem expor dados de outros usuários.
2. **Given** que o episódio não possui URL de mídia baixável, **When** eu abro a página, **Then** a ação de “baixar” não aparece (ou aparece desabilitada com explicação).
3. **Given** que estou na página do episódio, **When** eu clico em “compartilhar”, **Then** eu obtenho um link compartilhável para a página do episódio.

---

### User Story 3 - Favoritar e ver histórico de ouvidas (Priority: P3)

Como usuário, eu quero adicionar/remover o episódio dos favoritos e, quando possível, ver um histórico de ouvidas, para lembrar e gerenciar o que eu acompanho.

**Why this priority**: Complementa a experiência com preferências e contexto adicional, mas não bloqueia o uso principal (ver detalhe e progresso).

**Independent Test**: Pode ser testado favoritando/desfavoritando o episódio e recarregando a página para verificar persistência; para histórico, validar que um estado vazio é mostrado quando não houver dados.

**Acceptance Scenarios**:

1. **Given** que estou autenticado e o episódio existe, **When** eu marco como favorito, **Then** o estado permanece ao recarregar a página.
2. **Given** que eu removo o episódio dos favoritos, **When** eu recarrego a página, **Then** ele deixa de aparecer como favorito.
3. **Given** que existe histórico de ouvidas para o episódio, **When** eu abro a página, **Then** eu vejo uma lista simples de eventos (ex.: data/hora), sem expor dados de outros usuários.
4. **Given** que não existe histórico disponível, **When** eu abro a página, **Then** eu vejo um estado vazio apropriado para histórico.

---

### Edge Cases

- Episódio sem descrição, sem data de lançamento ou sem duração: página continua útil e não exibe campos vazios de forma confusa.
- Progresso desconhecido ou parcial: UI exibe estado “desconhecido” sem erros.
- Episódio com descrição muito longa: layout permanece estável e legível em mobile.
- Episódio com URL não baixável: ação de download não induz erro (oculta ou desabilita).
- Episódio removido/indisponível: página retorna 404 com mensagem amigável.
- Usuário não autenticado: acesso redireciona para login.

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: The system MUST provide an episode detail page reachable from the podcast episode list.
- **FR-002**: The episode detail page MUST display episode details: title, description (when present), release date/time (when present), image (or placeholder), and links relevant to the episode (when present).
- **FR-003**: The system MUST display episode progress for the authenticated user when progress data exists, including “time watched/listened” and “total time” when available.
- **FR-004**: The episode detail page MUST provide a download action when a downloadable media URL exists for the episode; otherwise it MUST not mislead the user (hidden or clearly disabled).
- **FR-005**: The episode detail page MUST provide a share action that yields a shareable link to the episode detail page.
- **FR-006**: The system MUST allow the authenticated user to favorite/unfavorite the episode from the detail page.
- **FR-007**: The system MUST persist the favorite state per user and episode and reflect it on subsequent page loads.
- **FR-008**: The episode detail page SHOULD show a listening history section when history data exists for the episode; when it does not exist, the page MUST show an appropriate empty state.
- **FR-009**: The system MUST return a 404 with a friendly message when the episode does not exist.
- **FR-010**: All user-visible strings introduced by this feature MUST be localizable (multilingual support consistent with the rest of the site).

### Non-Functional Requirements *(mandatory)*

- **NFR-001**: Verification evidence MUST include automated tests covering: render for existing episode, 404 for missing episode, favorite toggle, download action visibility rules, and share link availability.
- **NFR-002**: Access control MUST ensure only authenticated users can view the page and perform actions; user-specific progress/history MUST NOT leak across accounts.
- **NFR-003**: The episode detail page MUST be responsive on common mobile screen sizes without horizontal scrolling.
- **NFR-004**: The page should load within 2 seconds for typical episodes, and interactions (favorite toggle) should complete without noticeable delay for typical usage.

### Key Entities *(include if feature involves data)*

- **Episode**: A single episode belonging to a podcast feed, with metadata such as title, description, release time, and image.
- **Episode Progress**: Per-user progress information for an episode (watched/listened time, total time when available).
- **Favorite Episode**: A per-user favorite marker for a given episode.
- **Listening History Event**: A per-user record of listening activity for the episode (when available).

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: A logged-in user can open an episode detail page and see the episode metadata and progress (when available) within 2 seconds for typical usage.
- **SC-002**: Favoriting/unfavoriting an episode persists correctly and is reflected on reload at least 99% of the time (validated by tests).
- **SC-003**: The download action is shown only when appropriate (0 false positives in tests for “no downloadable media URL” cases).
- **SC-004**: 95% of manual checks on mobile-width layouts show no horizontal scrolling and no broken visual states.

## Assumptions

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right assumptions based on reasonable defaults
  chosen when the feature description did not specify certain details.
-->

- Existing authentication and locale handling will be reused (unauthenticated users are redirected to login).
- Episode identifiers are stable internal IDs and can be used to route to a specific episode detail page.
- “Download episode” means providing a direct download only when a downloadable media URL is known for the episode; otherwise, the UI will hide or clearly disable the action.
- Share action provides a stable link to the episode detail page; deep integration with OS-native share sheets is out of scope.
- Listening history may not be available for all episodes; when unavailable, the page will show an empty state without errors.
- The page follows existing UI patterns: multilingual copy, placeholder images, and mobile-friendly layout.

## Constitution Alignment *(mandatory)*

- **Slice Integrity**: US1 delivers the core value (episode detail + progress). US2 adds download/share actions without blocking US1. US3 adds favorites and optional listening history as an incremental enhancement.
- **Branch Plan**: Implementation happens on `019-episode-detail-page`, created from `main`.
- **Verification Plan**: Before merge, run `uv run pytest`, `uv run ruff check .`, `uv run mypy .`, and `uv run bandit -r app -c pyproject.toml`, plus targeted tests for page rendering and actions.
- **Quality Gate Strategy**: Fix lint/typing/security issues at the source; do not rely on `# noqa`/`# nosec` as shortcuts.
- **Review Readiness**: PR must summarize the new episode detail route, UI states (missing data, placeholders), favorite toggle behavior, and verification evidence.
- **Security/Simplicity Notes**: Progress and history are user-specific; the plan must ensure strict account isolation and avoid introducing unnecessary new dependencies.
