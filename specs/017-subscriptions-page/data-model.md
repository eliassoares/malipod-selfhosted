# Data Model: Subscriptions Page

**Feature**: `017-subscriptions-page` | **Date**: 2026-04-21

## Scope

Este feature introduz:
- 1 coluna nova em `episodes` para suportar imagem/placeholder por episódio
- defaults/normalização para garantir que `podcast_feeds.logo_url` e `episodes.logo_url`
  nunca fiquem vazios (quando não houver imagem real disponível)
- preferências de UI persistidas em `account_settings.settings`

## Existing Entities (relevant)

### `podcast_feeds` (`PodcastFeedModel`)

Campos relevantes:
- `feed_url` (único)
- `title`
- `logo_url` (atualmente pode ser `NULL`)

Uso no feature:
- base da listagem de subscrições.
- `logo_url` deve sempre renderizar uma imagem válida no SSR (imagem do feed ou placeholder).

### `device_subscriptions` (`DeviceSubscriptionModel`)

Campos relevantes:
- `device_pk` (FK devices)
- `feed_id` (FK podcast_feeds)
- `unsubscribed_at` (soft-unsub)

Uso no feature:
- fonte da relação “usuário segue feed”: listagem deve considerar apenas `unsubscribed_at IS NULL`
  e deduplicar feeds entre múltiplos devices do mesmo usuário.

### `episodes` (`EpisodeModel`)

Campos relevantes:
- `feed_id` (FK podcast_feeds)
- `episode_url` (único)
- `title`
- `released_at`

Uso no feature:
- agregações por feed:
  - `episode_count`: `COUNT(episodes.id)`
  - `last_episode_at`: `MAX(episodes.released_at)`

## Changes

### 1) Add `episodes.logo_url`

- **Table**: `episodes`
- **Column**: `logo_url` (string/URL)
- **Default**: placeholder aleatório (entre 2 imagens) quando a imagem real for desconhecida/ausente.

### 2) Enforce placeholder defaults for `podcast_feeds.logo_url`

Mesmo já existindo, o valor de `logo_url` não deve permanecer `NULL` quando o feed não tem imagem.

Implementação prevista (a definir nos tasks):
- setar placeholder no momento de criação/import do feed
- opcionalmente, migração/backfill para feeds antigos com `logo_url IS NULL`

### 3) UI preferences in `account_settings.settings`

Chaves propostas:
- `subscriptions.view_mode`: `"list"` | `"grid"`
- `subscriptions.sort`: `"recent"` | `"oldest"`

Sem nova tabela: reaproveitar o JSON já existente.
