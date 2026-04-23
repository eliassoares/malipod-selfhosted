# Feature Specification: User Metrics

**Feature Branch**: `020-user-metrics`
**Created**: 2026-04-23
**Status**: Draft
**Input**: User description: "Gostaria de melhorar algumas métricas que já temos, e criar uma página de métricas do usuário. Melhorias no header do podcast (/podcast/{id}) e na página do episódio (/episode/{id}), além de uma nova página /user/{nick}/stats com cards e rankings. Adicionar 'Métricas' no menu entre Subscrições e Sair."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver métricas do usuário (Priority: P1)

Como usuário autenticado, eu quero abrir uma página de métricas do meu perfil, para entender meus hábitos e meus podcasts mais relevantes em um único lugar.

**Why this priority**: Consolida as informações cross-podcast que não cabem em páginas individuais e cria valor imediato mesmo sem refinamentos nas demais páginas.

**Independent Test**: Pode ser testado autenticando, acessando `/user/{nick}/stats`, verificando cards de destaque, rankings Top 5 e estados vazios (sem eventos de escuta).

**Acceptance Scenarios**:

1. **Given** que estou autenticado e acessando minhas métricas, **When** eu abro `/user/{meu_nick}/stats`, **Then** eu vejo cards com totais (horas ouvidas, episódios concluídos, podcasts seguidos) e rankings Top 5 por tempo e por episódios concluídos.
2. **Given** que estou autenticado mas não tenho histórico de escuta suficiente, **When** eu abro `/user/{meu_nick}/stats`, **Then** a página mostra estados vazios claros (ex.: “sem dados ainda”) em rankings e seções temporais.
3. **Given** que tento acessar as métricas de outro usuário, **When** eu abro `/user/{outro_nick}/stats`, **Then** eu recebo 404 (ou equivalente) sem vazar informações de terceiros.

---

### User Story 2 - Ver métricas do podcast (Priority: P2)

Como usuário autenticado, eu quero ver métricas específicas de um podcast no header da página do podcast, para entender rapidamente meu engajamento naquele conteúdo.

**Why this priority**: A página do podcast já é um ponto natural de decisão (“continuar ouvindo?”, “o que falta?”), então métricas rápidas melhoram a utilidade sem adicionar fluxo novo.

**Independent Test**: Pode ser testado com um podcast com episódios e eventos de play, verificando que os novos campos aparecem e respeitam estado “sem dados”.

**Acceptance Scenarios**:

1. **Given** que estou autenticado e o podcast existe, **When** eu abro `/podcast/{id}`, **Then** eu vejo no header: taxa de conclusão, episódios em progresso e data do último episódio ouvido (quando houver dados).
2. **Given** que eu ainda não ouvi nada daquele podcast, **When** eu abro `/podcast/{id}`, **Then** métricas dependentes de play exibem estado “sem dados” sem quebrar o layout.

---

### User Story 3 - Ver métricas do episódio (Priority: P3)

Como usuário autenticado, eu quero ver métricas detalhadas do episódio, para entender meu progresso, frequência de escuta e informações sobre favoritos.

**Why this priority**: Complementa a página existente e adiciona contexto útil (quantas vezes toquei, quando comecei, quando ouvi por último), mas não bloqueia as métricas do usuário.

**Independent Test**: Pode ser testado com um episódio com eventos de play e favorito, validando contagem de plays, primeiras/últimas datas e texto de progresso “X de Y”.

**Acceptance Scenarios**:

1. **Given** que estou autenticado e tenho progresso no episódio, **When** eu abro `/episode/{id}`, **Then** eu vejo um texto de progresso “XX% (A de B)” além da barra.
2. **Given** que existem eventos de play do episódio, **When** eu abro `/episode/{id}`, **Then** eu vejo “vezes reproduzido”, data do primeiro play e do último play.
3. **Given** que o episódio está favoritado, **When** eu abro `/episode/{id}`, **Then** eu vejo também quando ele foi favoritado.

---

### Edge Cases

- Usuário autenticado sem nenhum evento de play: rankings e temporal mostram estado vazio amigável.
- Podcast com episódios mas sem plays: taxa de conclusão e último episódio ouvido mostram estado “sem dados”.
- Episódio sem `total` conhecido: texto “A de B” não aparece; UI mostra apenas o que for possível.
- Eventos com timestamps inconsistentes: streak/temporal pode ser ocultado ou exibido como “indisponível” sem erro.
- Tentativa de acessar `/user/{nick}/stats` de outro usuário: retorna 404 sem revelar existência do usuário.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a user metrics page at `/user/{nickname}/stats` for authenticated users.
- **FR-002**: The system MUST prevent cross-account access to `/user/{nickname}/stats` (only the owner can view); unauthorized access MUST not leak third-party data.
- **FR-003**: The user metrics page MUST display highlight cards:
  - total time listened (hours)
  - total completed episodes
  - total followed podcasts
- **FR-004**: The user metrics page SHOULD display an “active days streak” when there is sufficient reliable timestamp data; otherwise it MUST display an explicit empty/disabled state.
- **FR-005**: The user metrics page MUST display rankings:
  - Top 5 podcasts by time listened
  - Top 5 podcasts by completed episodes
  Rankings MUST provide a clear empty state when there is no data.
- **FR-006**: The user metrics page MAY display temporal insights when data exists:
  - hours listened per month (bar chart)
  - preferred listening hour
  - most active weekday
  When there is insufficient data, the page MUST show a clear empty state.
- **FR-007**: The global authenticated navigation MUST include a “Metrics/Métricas/Métricas” item between “Subscriptions” and “Logout”, pointing to `/user/{nickname}/stats`.

- **FR-008**: The podcast page header (`/podcast/{id}`) MUST display:
  - completion rate (e.g., “72% of episodes completed”)
  - number of episodes in progress
  - last played date for that podcast (when available)
  and MUST keep existing metrics intact.
- **FR-009**: The episode page (`/episode/{id}`) MUST display textual progress values alongside the progress bar:
  - percentage
  - listened/total time when both values exist (e.g., “32min of 45min”)
- **FR-010**: The episode page MUST display listening activity metrics derived from play events:
  - play count
  - first play date/time (when available)
  - last play date/time (when available)
- **FR-011**: When an episode is favorited, the episode page MUST display the favorite timestamp (e.g., “Favorited on YYYY-MM-DD”).

### Non-Functional Requirements *(mandatory)*

- **NFR-001**: Verification evidence MUST include automated tests that cover:
  - `/user/{nick}/stats` access control, rendering, and empty states
  - podcast header metrics rendering and empty states
  - episode metrics rendering (progress text, plays, first/last)
  plus static checks used in the project quality gate.
- **NFR-002**: Metrics pages MUST respect privacy: a user MUST never see another user’s aggregates or event history through UI or endpoints.
- **NFR-003**: Metrics computation MUST remain responsive for typical personal usage; pages MUST render within a reasonable time with hundreds of episodes and play events.

### Key Entities *(include if feature involves data)*

- **Listening Event**: A user’s play-related activity record with timestamp and optional position/total.
- **Progress Snapshot**: The latest known progress (position/total) for an episode, shown on the episode page.
- **Favorite Marker**: A user’s favorite state for an episode, including when it was favorited.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An authenticated user can open `/user/{nick}/stats` and understand totals + top podcasts without leaving the page.
- **SC-002**: Metrics pages show clear empty states when data is missing, with no broken layouts on mobile.
- **SC-003**: Users cannot access metrics for other accounts (validated by automated tests for cross-account attempts).
- **SC-004**: At least 90% of the metrics labels and UI strings used by these pages are translated across supported languages, with no missing-key fallbacks visible in normal flows.

## Assumptions

- “Completed episode” follows the same user-visible rule already used elsewhere in the product (high completion ratio or near-the-end threshold), to keep mental models consistent.
- “Time listened” aggregates are based on de-duplicated per-episode progress (avoid double-counting repeated plays when computing totals), unless future product decisions prefer “total play time”.
- Temporal insights and streak are “best-effort” and can remain hidden/disabled until timestamps are reliable enough to avoid misleading results.
- Metrics use the user’s selected language and are mobile-friendly following existing site patterns.

## Constitution Alignment *(mandatory)*

- **Slice Integrity**:
  - US1 (User metrics page) is independently valuable and testable as a cross-podcast dashboard.
  - US2 (Podcast header metrics) improves a single page without depending on the user stats page.
  - US3 (Episode metrics) improves a single page without depending on US1/US2.
- **Branch Plan**: The feature will be implemented on a branch created from `main` (`020-user-metrics`).
- **Verification Plan**: Run the repository checks and add/extend tests for the three user stories, including empty states and access control.
- **Quality Gate Strategy**: Resolve lint/typing/security findings via code changes and tests rather than inline suppressions.
- **Review Readiness**: The pull request must summarize added/changed metrics, definitions used (completion/time listened), tests added, and any deferred temporal/streak behaviors.
- **Security/Simplicity Notes**: Metrics aggregation must not expose other users’ data; prefer simple, explainable calculations and explicit empty states over complex heuristics.
