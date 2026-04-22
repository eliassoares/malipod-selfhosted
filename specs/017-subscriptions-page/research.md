# Research: Subscriptions Page

**Feature**: `017-subscriptions-page` | **Date**: 2026-04-21

## Goal

Definir como implementar a página SSR de subscrições seguindo o padrão do projeto
(auth + i18n + layout), quais queries/entidades serão necessárias e como tratar
persistência de preferências e placeholders de imagem sem introduzir complexidade
desnecessária.

## Findings (codebase)

### Existing SSR patterns (auth + i18n + layout)

- Layout base: `app/templates/base.html` inclui `partials/head.html`, `partials/topbar.html` e `partials/footer.html`.
- SSR routes existentes:
  - `app/api/routes/site.py` (home) resolve `locale` + `copy` e passa `current_user`.
  - `app/api/routes/profile_site.py` aplica o padrão de autorização: redireciona deslogado, e retorna 404 se o nickname na URL não corresponde ao usuário logado.
- i18n atual: strings vêm de `copy = LocalizationService.build_copy(locale)` (dicionário),
  consumidas em templates como `copy["nav.home"]`.

**Decision**: implementar `GET /user/subscriptions/{username}` replicando o padrão do
`profile_site.py` (redirect/404) e passando `locale`, `copy`, `supported_locales` e `current_user`
no contexto do template.

### Existing subscription data and OPML rendering

- Assinaturas estão em:
  - `device_subscriptions` (associação device → feed) via `DeviceSubscriptionModel`
  - `podcast_feeds` via `PodcastFeedModel` (inclui `feed_url`, `title`, `logo_url`, etc.)
- Há renderizador OPML pronto em `app/services/subscription_formats.py` (mídia `application/xml`)
  que recebe `SubscriptionItem` (url, title, website, logo_url…).

**Decision**: export OPML na página SSR deve reutilizar `SubscriptionFormatService.render(...)`
para garantir compatibilidade e evitar duplicar lógica.

### Preferências do usuário

- Há storage genérico em `account_settings.settings` (`AccountSettingModel`) e serviço pronto:
  `app/services/settings.py#SettingsService`.
- Já existe API de settings (`app/api/routes/settings_api.py`) — útil para clients; para SSR,
  dá para chamar o serviço diretamente (ou expor um endpoint simples para o site).

**Decision**: guardar a preferência de visualização (list/grid) e ordenação default como chaves
em `account_settings.settings` (ex.: `subscriptions.view_mode`, `subscriptions.sort`).

### Episódios e agregações necessárias

- Episódios estão em `episodes` via `EpisodeModel` (tem `released_at`, não tem imagem ainda).

**Decision**:
- Contagem de episódios por feed: `COUNT(episodes.id)` por `feed_id`.
- Último episódio por feed: `MAX(episodes.released_at)` por `feed_id`.
- Implementar query agregada no backend (SQLAlchemy) para evitar N+1.

### Placeholder images

- Existe `app/static/` (vazio hoje) e o projeto já serve static assets.
- `podcast_feeds.logo_url` existe mas é `nullable` e atualmente é salvo como `None`.
- `episodes` não tem `logo_url`.

**Decision**:
- Mover `lilith.png` e `malte.png` para `app/static/placeholders/`.
- Definir estratégia: quando `logo_url` for ausente/None na criação/import, setar automaticamente
  para um placeholder escolhido aleatoriamente entre os dois.
- Adicionar `episodes.logo_url` e aplicar a mesma regra.

## Key Decisions

### Page contract (SSR)

- Template: `app/templates/subscriptions/index.html` estende `base.html`.
- Context mínimo: `locale`, `copy`, `supported_locales`, `current_user`, `page_title`,
  lista de podcasts com `title`, `feed_url`, `logo_url`, `episode_count`, `last_episode_at`.

### Sorting, filtering, and view mode

- Search: filtro por `PodcastFeedModel.title` (case-insensitive) e opcionalmente por URL do feed.
- Sort:
  - `recent`: `last_episode_at DESC NULLS LAST`
  - `oldest`: `last_episode_at ASC NULLS FIRST`
- View mode: `list` | `grid` persistido em `account_settings`.

### Add-by-URL and background processing

O codebase ainda não tem um job runner explicitamente (celery/arq/rq etc.).

**Decision** (MVP): o SSR endpoint de “add por URL” deve:
- validar e sanitizar input (reutilizar `sanitize_subscription_url`)
- registrar a subscrição para todos os devices do usuário usando `SubscriptionService` (ou um service dedicado)
- disparar um “background kickoff” (a definir na fase de tasks) para:
  - validar o feed remotamente
  - importar episódios e atualizar metadados (título, imagem, etc.)

O mecanismo de execução (BackgroundTasks vs worker externo) será decidido na fase de tasks,
com foco em simplicidade e segurança (rede como input hostil).
