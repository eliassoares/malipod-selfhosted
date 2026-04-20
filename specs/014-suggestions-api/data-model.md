# Data Model: Suggestions API

**Feature**: `014-suggestions-api` | **Date**: 2026-04-20

## Scope

Sem novas tabelas. A Suggestions API deriva tudo de assinaturas ativas já existentes.

## Existing Entities (runtime)

### User

- Fonte: `app/db/models/user.py::UserModel`
- Uso: identificar o usuário autenticado e excluir suas assinaturas das sugestões.

### Device

- Fonte: `app/db/models/device.py::DeviceModel`
- Uso: ligar assinaturas (`DeviceSubscriptionModel`) ao usuário (`DeviceModel.user_id`).

### DeviceSubscription

- Fonte: `app/db/models/podcast.py::DeviceSubscriptionModel`
- Campos relevantes:
  - `feed_id`
  - `device_pk`
  - `unsubscribed_at` (somente `NULL` conta como assinatura ativa)
- Uso:
  - determinar quais feeds fazem parte do catálogo (feeds com pelo menos 1 assinatura ativa)
  - excluir feeds já assinados pelo usuário atual
  - calcular popularidade (contagem de usuários distintos por feed)

### PodcastFeed

- Fonte: `app/db/models/podcast.py::PodcastFeedModel`
- Campos relevantes:
  - `feed_url`, `title`, `author`, `description`, `logo_url`, `website`
- Uso: metadados retornados no JSON e utilizados para OPML/TXT.

## Derived Models (API payloads)

### PodcastDirectoryItem (response item)

- Fonte: `app/schemas/directory.py::PodcastDirectoryItem`
- Campos (compatíveis com FR-009):
  - `url`, `title`, `author`, `description`, `subscribers`, `logo_url`, `website`, `mygpo_link`

## Query Model (suggestions)

**Input**:
- `current_user.id`
- `number` (1..100)

**Algorithm**:
1. Subquery `subscribers_per_feed`:
   - contar `distinct(UserModel.id)` por `DeviceSubscriptionModel.feed_id`
   - filtrar `DeviceSubscriptionModel.unsubscribed_at IS NULL`
2. Subquery `user_active_subscriptions`:
   - selecionar `DeviceSubscriptionModel.feed_id` onde `UserModel.id == current_user.id` e assinatura ativa
3. Query principal:
   - `PodcastFeedModel` join `subscribers_per_feed`
   - filtrar `PodcastFeedModel.id NOT IN user_active_subscriptions`
   - ordenar por `subscribers desc, feed_url asc`
   - limitar `number`

**Output**:
- lista de `PodcastDirectoryItem` (com `subscribers` do subquery e `mygpo_link` baseado em `base_url`).
