# Feature Specification: Subscriptions Page

**Feature Branch**: `017-subscriptions-page`
**Created**: 2026-04-21
**Status**: Draft
**Input**: User description: "Quero criar a página de subinscrições (/user/subscriptions/{username}) para mostrar e gerenciar os podcasts que o usuário segue (listar, adicionar por URL com processamento assíncrono, alternar lista/grid com preferência lembrada, ordenar por mais antigos/mais recentes baseado no último episódio, exportar OPML, pesquisar). Também precisamos de placeholders de imagem para podcasts/episódios sem imagem."

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

### User Story 1 - Ver minhas subscrições (Priority: P1)

Como usuário autenticado, eu quero ver uma página com os podcasts que eu sigo, para acompanhar rapidamente o que estou seguindo e quando saiu o último episódio.

**Why this priority**: Essa é a função principal da página (“minhas subscrições”) e dá valor imediato mesmo sem ações de gerenciamento.

**Independent Test**: Pode ser testado apenas acessando a rota da página com um usuário que segue 0+ podcasts e verificando a lista e os metadados exibidos.

**Acceptance Scenarios**:

1. **Given** que estou autenticado e sigo 3 podcasts, **When** eu acesso a página de subscrições, **Then** eu vejo 3 itens com nome, imagem (ou placeholder), quantidade de episódios e o “tempo do último episódio”.
2. **Given** que estou autenticado e não sigo nenhum podcast, **When** eu acesso a página de subscrições, **Then** eu vejo um estado vazio com chamada clara para adicionar um podcast.
3. **Given** que um podcast (ou seus episódios) não possui imagem, **When** eu vejo a lista, **Then** o item usa uma imagem de placeholder sem quebrar o layout.

---

### User Story 2 - Buscar, ordenar e escolher visualização (Priority: P2)

Como usuário, eu quero pesquisar meus podcasts, ordenar a lista e escolher entre visualização em lista ou grid, para encontrar rapidamente o que preciso do jeito que eu prefiro.

**Why this priority**: Melhora muito a usabilidade quando o usuário segue muitos podcasts, sem depender de integrações externas.

**Independent Test**: Pode ser testado com um usuário com várias subscrições, verificando busca, ordenação, alternância de visualização e persistência da preferência.

**Acceptance Scenarios**:

1. **Given** que sigo podcasts com nomes diferentes, **When** eu pesquiso por um termo, **Then** apenas os podcasts correspondentes aparecem.
2. **Given** que sigo podcasts com “último episódio” em datas diferentes, **When** eu ordeno por “mais recentes”, **Then** os primeiros itens são os que têm o último episódio mais recente.
3. **Given** que sigo podcasts com “último episódio” em datas diferentes, **When** eu ordeno por “mais antigos”, **Then** os primeiros itens são os que têm o último episódio mais antigo.
4. **Given** que alterno de lista para grid (ou vice-versa), **When** eu volto à página depois, **Then** a página lembra e aplica minha preferência.

---

### User Story 3 - Adicionar podcast por URL (Priority: P3)

Como usuário, eu quero adicionar um podcast informando a URL do feed, para seguir novos podcasts sem depender de catálogos externos.

**Why this priority**: Amplia o valor da página e habilita crescimento do uso, mas depende de processamento assíncrono e validações (maior risco/complexidade).

**Independent Test**: Pode ser testado submetendo uma URL válida e outra inválida e verificando estados (pendente, sucesso, erro) sem exigir que todos os metadados estejam completos imediatamente.

**Acceptance Scenarios**:

1. **Given** que estou autenticado, **When** eu envio uma URL de feed válida, **Then** a página confirma o envio e mostra o podcast em estado “processando” (ou equivalente) até concluir.
2. **Given** que envio uma URL inválida (ou que não é feed de podcast), **When** eu confirmo, **Then** eu vejo um erro claro e nenhuma subscrição duplicada é criada.
3. **Given** que eu adiciono um podcast que já sigo, **When** eu tento adicionar novamente, **Then** o sistema evita duplicação e informa que o podcast já está na minha lista.

---

### User Story 4 - Exportar minhas subscrições em OPML (Priority: P4)

Como usuário, eu quero exportar minhas subscrições em OPML, para migrar/backup das minhas assinaturas em outros apps.

**Why this priority**: Valor alto, mas é uma ação pontual e pode vir após o núcleo de navegação/gerenciamento.

**Independent Test**: Pode ser testado gerando o arquivo e validando que ele contém todos os feeds seguidos pelo usuário.

**Acceptance Scenarios**:

1. **Given** que sigo 5 podcasts, **When** eu clico para exportar OPML, **Then** um arquivo OPML é baixado contendo os 5 podcasts (com título e URL de feed).
2. **Given** que não sigo nenhum podcast, **When** eu exporto OPML, **Then** eu ainda recebo um OPML válido (vazio) ou uma mensagem clara explicando que não há itens a exportar.

### Edge Cases

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right edge cases.
-->

- Lista com muitos itens (ex.: 1.000 podcasts): paginação/scroll, busca e ordenação continuam utilizáveis.
- Podcasts sem episódios conhecidos ainda: exibição não quebra; “último episódio” tem fallback claro.
- Falha no processamento assíncrono (timeout, erro de validação, feed indisponível): usuário vê erro e caminho para tentar novamente.
- OPML export com caracteres especiais (acentos, símbolos): arquivo permanece válido e importável.
- Acesso indevido: tentar acessar `/user/subscriptions/{username}` de outro usuário não deve expor dados.

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: System MUST provide a “Minhas subscrições” page at `/user/subscriptions/{username}` for authenticated users.
- **FR-002**: System MUST restrict access so only the owner can view their subscriptions for a given `{username}`.
- **FR-003**: System MUST show the podcasts the user follows, including: podcast name, podcast image (or placeholder), episode count, and “time of last episode” (date/time or human-readable relative time).
- **FR-004**: System MUST provide a mobile-friendly layout and follow the same UI structure/patterns as other user pages (navigation, spacing, typography, states).
- **FR-005**: System MUST support the app’s existing multilingual behavior: all user-visible strings on the page are localizable.
- **FR-006**: Users MUST be able to switch between list view and grid view.
- **FR-007**: System MUST remember the user’s view choice across sessions (so it persists when the user returns).
- **FR-008**: Users MUST be able to search/filter their followed podcasts by name (and optionally by feed URL).
- **FR-009**: Users MUST be able to sort the list by “most recent” and “oldest”, based on the last episode publish date/time.
- **FR-010**: Users MUST be able to export their followed podcasts as an OPML file.
- **FR-011**: Users MUST be able to add a new podcast by providing a feed URL.
- **FR-012**: System MUST validate the submitted URL enough to prevent obvious invalid input and must provide a user-friendly error message on failure.
- **FR-013**: After a successful submission, system MUST process the podcast asynchronously and, when processing completes, the podcast must appear with updated metadata and its episodes must be available to the user’s devices.
- **FR-014**: System MUST handle missing images for podcasts and episodes by assigning a placeholder image; when a placeholder is assigned, it should be chosen randomly from two provided placeholder options to avoid a monotonous look.

*Example of marking unclear requirements:*

*(No clarification markers needed for this feature at this stage.)*

### Non-Functional Requirements *(mandatory)*

- **NFR-001**: Verification evidence MUST include automated tests for the main user flows (view page, search/sort, add by URL, export OPML) plus static checks already used in the repository.
- **NFR-002**: Security/privacy constraints MUST ensure subscriptions are not exposed to other users and that URL submission/processing does not allow users to trigger unsafe network access.
- **NFR-003**: The page MUST remain usable on common mobile screen sizes, including accessible tap targets and readable typography without horizontal scrolling.
- **NFR-004**: For users with up to 1.000 subscriptions, the page MUST remain responsive: searching and sorting should feel “instant” for the user (target: < 1 second perceived latency).

### Key Entities *(include if feature involves data)*

- **User**: The authenticated account that owns subscriptions and preferences.
- **Subscription**: A relationship between a user and a podcast feed (followed/unfollowed).
- **Podcast**: A feed the user follows; has name, feed URL, optional image, and derived “last episode” info.
- **Episode**: An item belonging to a podcast; has publish time and optional image.
- **Device**: A user-owned device that should receive the user’s subscriptions and episodes once processing completes.
- **View Preference**: The user’s chosen view mode (list/grid) for the subscriptions page.
- **Export (OPML)**: A downloadable representation of the user’s subscriptions.

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: A user with 0+ subscriptions can open the page and see the correct list (or empty state) within 2 seconds for typical usage.
- **SC-002**: At least 95% of searches return filtered results within 1 second for a user with up to 1.000 subscriptions.
- **SC-003**: A user can switch list/grid and sees the same choice preserved on the next visit at least 99% of the time.
- **SC-004**: A user can export OPML and the exported file includes 100% of their followed podcasts with correct feed URLs.
- **SC-005**: After submitting a valid feed URL, the user sees clear progress feedback, and the subscription becomes fully available (metadata + episodes) within 5 minutes for typical feeds.

## Assumptions

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right assumptions based on reasonable defaults
  chosen when the feature description did not specify certain details.
-->

- Users are already authenticated using the app’s existing authentication flow.
- The system already stores (or can derive) each subscription’s episode count and last episode publish time.
- Asynchronous processing exists (or will be introduced) to validate feeds and sync updates without blocking the user’s request.
- The app already has a localization mechanism; this page will use it for all visible strings.
- Two placeholder images already exist and can be served as static assets; missing podcast/episode images will use one of them chosen randomly when a placeholder is assigned.
- The route includes `{username}` for URL readability, but it is assumed the page displays only the authenticated user’s data (no public sharing of subscriptions in v1).

## Constitution Alignment *(mandatory)*

- **Slice Integrity**: P1 delivers value by providing a clear view of subscriptions even without management actions; P2 improves organization without needing add/export; P3 adds acquisition via URL without depending on export; P4 enables migration/backup as a standalone action.
- **Branch Plan**: Implementation happens on `017-subscriptions-page`, created from `main`.
- **Verification Plan**: Automated tests cover the main scenarios (view, empty state, search/sort, add URL validation + async status, OPML export). Static checks (lint/format/type where applicable) pass in CI.
- **Quality Gate Strategy**: Address any lint/security findings by fixing root causes; do not rely on inline suppressions like `# noqa` / `# nosec`.
- **Review Readiness**: PR summarizes user-visible behavior, route, UI states (loading/empty/error), i18n coverage, and test evidence for each user story.
- **Security/Simplicity Notes**: URL submission and background processing are the main risk area; planning must justify safe validation and ensure subscription privacy by default.
