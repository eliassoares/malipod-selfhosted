# Feature Specification: Podcast Detail Page

**Feature Branch**: `018-podcast-detail-page`
**Created**: 2026-04-22
**Status**: Draft
**Input**: User description: "Criar a página de detalhe do podcast em `/podcast/{ID_PODCAST}` com metadata e lista de episódios (ordenável por data), com ações de inscrever e favoritar. Adicionar na página de subscrições um filtro para mostrar apenas podcasts favoritos."

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

### User Story 1 - Ver detalhe do podcast e seus episódios (Priority: P1)

Como usuário autenticado, eu quero abrir uma página de detalhe de um podcast, para ver suas informações principais e a lista completa de episódios.

**Why this priority**: É o núcleo do feature e habilita o restante (ordenar, inscrever, favoritar) dentro do contexto do podcast.

**Independent Test**: Pode ser testado acessando `/podcast/{ID_PODCAST}` para um podcast existente e validando a renderização e estados de erro.

**Acceptance Scenarios**:

1. **Given** que estou autenticado e o podcast existe, **When** eu acesso `/podcast/{ID_PODCAST}`, **Then** eu vejo nome, descrição, website (quando existir), autor, categorias, imagem (ou placeholder) e a lista de episódios.
2. **Given** que estou autenticado e o podcast não existe, **When** eu acesso `/podcast/{ID_PODCAST}`, **Then** eu recebo uma resposta de “não encontrado” (404) com mensagem amigável.
3. **Given** que um podcast ou episódio não tem imagem, **When** eu vejo a página, **Then** uma imagem de placeholder é exibida sem quebrar o layout.

---

### User Story 2 - Ordenar episódios por data (Priority: P2)

Como usuário, eu quero ordenar a lista de episódios por data, para encontrar rapidamente os episódios mais novos ou mais antigos.

**Why this priority**: Com muitos episódios, ordenação é essencial para navegação e não depende de novas integrações.

**Independent Test**: Pode ser testado com episódios em datas diferentes e validando a ordem antes/depois da troca de ordenação.

**Acceptance Scenarios**:

1. **Given** que o podcast tem episódios com datas diferentes, **When** eu seleciono “mais recentes”, **Then** a lista ordena do mais recente para o mais antigo.
2. **Given** que o podcast tem episódios com datas diferentes, **When** eu seleciono “mais antigos”, **Then** a lista ordena do mais antigo para o mais recente.

---

### User Story 3 - Inscrever e favoritar podcast (Priority: P3)

Como usuário, eu quero me inscrever em um podcast quando ainda não estou inscrito e também marcar/desmarcar um podcast como favorito, para gerenciar melhor o que acompanho.

**Why this priority**: Aumenta o valor da página (ação) e habilita o filtro de favoritos na página de subscrições.

**Independent Test**: Pode ser testado abrindo a página de um podcast não inscrito, inscrevendo, e depois alternando favorito e verificando persistência.

**Acceptance Scenarios**:

1. **Given** que não estou inscrito no podcast, **When** eu abro `/podcast/{ID_PODCAST}`, **Then** eu vejo a opção de “inscrever”.
2. **Given** que eu clico em “inscrever”, **When** a ação conclui, **Then** eu passo a estar inscrito e a UI reflete o novo estado.
3. **Given** que eu marco um podcast como favorito, **When** eu volto para a página do podcast depois, **Then** o estado de favorito permanece.

---

### User Story 4 - Filtrar subscrições por favoritos (Priority: P4)

Como usuário, eu quero filtrar meus podcasts seguidos para ver apenas os favoritos, para focar nos podcasts que eu mais acompanho.

**Why this priority**: Melhora a organização da página existente de subscrições e depende do “favoritar podcast” estar disponível.

**Independent Test**: Pode ser testado marcando 2 podcasts como favoritos e validando que o filtro reduz a lista corretamente.

**Acceptance Scenarios**:

1. **Given** que sigo vários podcasts e tenho alguns favoritos, **When** eu ativo o filtro “somente favoritos” na página de subscrições, **Then** eu vejo apenas os podcasts marcados como favoritos.
2. **Given** que não tenho favoritos, **When** eu ativo o filtro “somente favoritos”, **Then** eu vejo um estado vazio adequado.

### Edge Cases

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right edge cases.
-->

- Podcast com descrição, autor, website ou categorias ausentes: página continua útil e não exibe campos vazios de forma confusa.
- Podcast com muitos episódios: paginação ou carregamento progressivo pode ser necessário; a página continua responsiva.
- Episódios com datas faltantes/invalidas: ordenação tem fallback consistente e não quebra a página.
- Usuário tenta acessar um podcast que não segue: a página ainda pode ser exibida, mas deve mostrar claramente o estado “não inscrito” e a ação de inscrever.
- Ações repetidas (favoritar/inscrever) não criam duplicatas nem levam o sistema a estados inconsistentes.

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: System MUST provide a podcast detail page at `/podcast/{ID_PODCAST}` for authenticated users.
- **FR-002**: System MUST show podcast metadata on the detail page: name/title, description, website (if present), author (if present), categories (if present), and image (or placeholder).
- **FR-003**: System MUST list all episodes for the podcast on the detail page, including at minimum: episode title, release date/time, and image (or placeholder).
- **FR-004**: Users MUST be able to sort episodes by date (most recent / oldest).
- **FR-005**: If the user is not subscribed to the podcast, the detail page MUST present a “subscribe” action.
- **FR-006**: The system MUST allow the user to mark/unmark a podcast as favorite from the podcast detail page.
- **FR-007**: The system MUST persist the favorite state per user and podcast.
- **FR-008**: The subscriptions page MUST provide a filter to show only favorite podcasts among the user’s followed podcasts.
- **FR-009**: The subscriptions page MUST remain mobile-friendly and consistent with existing UI patterns (layout, states, navigation).
- **FR-010**: All user-visible strings introduced by this feature MUST be localizable (multilingual support consistent with the rest of the site).

*Example of marking unclear requirements:*

*(No clarification markers needed for this feature at this stage.)*

### Non-Functional Requirements *(mandatory)*

- **NFR-001**: Verification evidence MUST include automated tests covering: podcast detail render, sorting, subscribe action visibility/behavior, favorite toggling, and favorites-only filter on subscriptions page.
- **NFR-002**: Access control MUST prevent unauthorized actions (subscribe/favorite) without an authenticated user.
- **NFR-003**: The feature MUST be responsive on common mobile screen sizes without horizontal scrolling.
- **NFR-004**: For podcasts with large episode lists, user interactions (sorting) should feel “instant” (target: < 1 second perceived latency for typical data sizes).

### Key Entities *(include if feature involves data)*

- **Podcast**: A podcast feed with metadata (title, description, website, author, categories, image).
- **Episode**: An episode belonging to a podcast with title, release timestamp, and image.
- **Subscription**: Relationship between user (and their devices) and a podcast.
- **Podcast Favorite**: Per-user favorite flag for a specific podcast.

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: A logged-in user can open `/podcast/{ID_PODCAST}` for an existing podcast and see metadata + episode list within 2 seconds for typical usage.
- **SC-002**: Sorting episodes updates the displayed order within 1 second perceived latency for typical podcasts.
- **SC-003**: Favorite toggling persists correctly and is reflected across pages at least 99% of the time.
- **SC-004**: The favorites-only filter on subscriptions page returns exactly the set of favorited podcasts for the user (0 false positives/negatives in tests).

## Assumptions

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right assumptions based on reasonable defaults
  chosen when the feature description did not specify certain details.
-->

- Users are authenticated using the existing session-based flow and site pages redirect to `/login` when not authenticated.
- `ID_PODCAST` in `/podcast/{ID_PODCAST}` refers to a stable internal identifier for the podcast feed (assumed numeric ID).
- Podcast metadata fields (author, categories, description, website, image) may be partially missing; the UI will handle absent fields gracefully.
- A “favorite” is private to the user and does not affect other users.
- The subscriptions page already exists and can be extended with one additional filter toggle without redesigning the whole page.

## Constitution Alignment *(mandatory)*

- **Slice Integrity**: P1 entrega valor ao exibir a página de detalhe e episódios; P2 melhora navegação com ordenação; P3 adiciona ações de inscrição/favoritar; P4 melhora a página de subscrições com filtro de favoritos.
- **Branch Plan**: Implementation happens on `018-podcast-detail-page`, created from `main`.
- **Verification Plan**: Automated tests cover page rendering, sort behavior, subscribe/favorite actions, and the favorites filter; repository quality gates pass before merge.
- **Quality Gate Strategy**: Fix root causes for lint/typing/security findings; do not rely on inline suppressions.
- **Review Readiness**: PR summarizes the new route, UI states, i18n coverage, data assumptions for `ID_PODCAST`, and verification evidence per user story.
- **Security/Simplicity Notes**: Favoriting/subscribing are state-changing actions; planning must ensure correct authorization and idempotency.
