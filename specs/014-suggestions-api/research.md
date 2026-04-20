# Research: Suggestions API

**Feature**: `014-suggestions-api` | **Date**: 2026-04-20

## Goal

Resolver dúvidas técnicas do plano e definir decisões implementáveis e consistentes
com o código existente (Directory API, auth e renderização OPML/TXT).

## Findings (codebase)

### Authentication (cookie + Basic)

- Existe autenticação por cookie de sessão em `app/api/deps.py#get_current_user`.
- Existe autenticação Basic reutilizável via `AuthService.authenticate_username(...)`.
- `authenticate_api_user(...)` valida também o `username` da rota (para endpoints que incluem `{username}` no path), o que não se aplica a `/suggestions/...` (não há username no path).

**Decision**: criar um helper específico para “usuário atual obrigatório” (cookie OU Basic) que não dependa de username no path, e que retorne `401` com `WWW-Authenticate: Basic` quando não autenticado.

**Rationale**: manter consistência com os endpoints existentes que suportam cookie e Basic, sem introduzir auth nova.

**Alternatives considered**:
- Exigir username no path: rejeitado por não estar no contrato do endpoint.
- Somente cookie: rejeitado por quebrar compatibilidade com Basic.

### Number validation (1–100)

- Há validador `validate_count_parameter(value, name=...)` em `app/core/security.py`.

**Decision**: reutilizar `validate_count_parameter(number, name="number")` e mapear `ValueError` para `400 Bad Request` na rota, igual ao Directory API.

### Formats (json|opml|txt)

- Há `SubscriptionFormatService` com `render(...)` que produz:
  - JSON: `application/json` (lista de objetos)
  - OPML: `application/xml`
  - TXT: `text/plain; charset=utf-8`
- Directory API (`/search` e `/toplist`) já usa `SubscriptionFormatService` para OPML/TXT, construindo `SubscriptionItem` a partir de `PodcastDirectoryItem`.

**Decision**: para `/suggestions`, seguir o mesmo padrão:
- `json`: retornar lista de `PodcastDirectoryItem` via `model_dump(exclude_none=True)`
- `opml`/`txt`: mapear para `SubscriptionItem` e renderizar com `SubscriptionFormatService`.

### Catalog + popularity query

- `DirectoryService` já implementa um subquery de contagem de assinantes distintos por feed ativo:
  - `DeviceSubscriptionModel` (feed_id, unsubscribed_at)
  - join `DeviceModel` → join `UserModel`
  - `count(distinct(UserModel.id))` agrupado por `feed_id`
- `DirectoryService.toplist(number)` usa esse subquery e ordena por subscribers desc.

**Decision**: implementar sugestões reutilizando a mesma fonte de verdade do catálogo:
- Considerar como candidatos apenas feeds com pelo menos 1 assinatura ativa (já garantido pelo subquery + join).
- Excluir feeds assinados pelo usuário atual (via subquery de `feed_id` filtrado por `UserModel.id == current_user.id` e `unsubscribed_at is NULL`).
- Ordenar por `subscribers desc, feed_url asc` e limitar por `number`.

**Rationale**: corresponde à spec e mantém consistência com o catálogo do servidor (Directory API).

**Alternatives considered**:
- Carregar toplist e filtrar em memória: rejeitado (menos eficiente e maior I/O).
- Manter service separado duplicando query: rejeitado (redundância e drift).

## Implementation Notes

- `mygpo_link` deve usar `base_url` configurado; `DirectoryService` já normaliza trailing slash e constrói o link (`build_podcast_mygpo_link`).
- Endpoint é read-only; não haverá migrations.
