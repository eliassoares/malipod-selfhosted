# Research: User Data Tools

**Feature**: `016-user-data-tools` | **Date**: 2026-04-20

## Goal

Definir o formato de snapshot JSON e regras de merge/import, usando as chaves
naturais e colunas de recência conforme as screenshots fornecidas, mantendo
segurança (escopo do usuário) e evitando dependências novas.

## Findings (codebase)

### Relevant tables (SQLAlchemy models)

- `users` (`app/db/models/user.py`)
- `account_settings`, `device_settings`, `podcast_settings`, `episode_settings` (`app/db/models/settings.py`)
- `devices` (`app/db/models/device.py`)
- `device_sync_groups` (`app/db/models/device_sync_group.py`)
- `podcast_feeds`, `episodes`, `device_subscriptions`, `subscription_change_events`,
  `episode_actions`, `episode_action_events`, `favorite_episodes`,
  `podcast_lists`, `podcast_list_items` (`app/db/models/podcast.py`)
- `authenticated_sessions` (`app/db/models/session.py`) — **não exportar/importar** (efêmero)

## Decisions

### Snapshot format (per-table fields)

**Decision**: exportar um JSON com um campo por tabela, onde cada campo contém
uma lista de objetos no formato “export-friendly” usando chaves naturais (ex.:
`feed_url`, `episode_url`, `device_id`) ao invés de IDs internos do banco.

**Rationale**: IDs variam entre instâncias e não são estáveis. As screenshots
definem chaves naturais por URL/string; isso simplifica restore.

### Table merge rules (natural key + recency)

**Decision**: para tabelas com recência (ex.: `updated_at`), importar com:
- localizar o registro via chave natural
- comparar timestamps pela coluna de recência da tabela
- se o do arquivo for **mais antigo ou igual** ao do banco: ignorar
- se for **mais recente**: atualizar

**Append-only events**:
- `subscription_change_events`: inserir apenas se não existe (chave natural inclui `created_at`)
- `episode_action_events`: inserir apenas se não existe (chave natural inclui `occurred_at`)

### Key/recency mapping (from screenshots)

| Table | Natural key (export/import) | Recency | Notes |
|------|------------------------------|---------|------|
| `users` | `email` (fallback: `nickname`) | `updated_at` | export sem hashes |
| `account_settings` | `user_id` (implicit) | `updated_at` | 1:1 com user |
| `devices` | (`user_id`, `device_id`) | `updated_at` | `device_id` é string do cliente |
| `device_sync_groups` | — | — | reconstruir a partir de devices importados |
| `device_settings` | (`user_id`, `device_id`) | `updated_at` | referencia device por `device_id` |
| `podcast_feeds` | `feed_url` | `updated_at` | global; não sobrescrever com mais velho |
| `episodes` | `episode_url` | `updated_at` | global; mesma lógica do feed |
| `device_subscriptions` | (`device_id`, `feed_url`) | `updated_at` | estado atual |
| `episode_actions` | (`user_id`, `episode_url`) | `occurred_at` | `occurred_at` mais confiável |
| `favorite_episodes` | (`user_id`, `episode_url`) | `updated_at` | |
| `subscription_change_events` | (`device_id`, `feed_url`, `operation`, `created_at`) | — | append-only |
| `episode_action_events` | (`episode_url`, `action`, `occurred_at`) | — | append-only |
| `podcast_lists` | (`user_id`, `name`) | `updated_at` | `name` é slug |
| `podcast_list_items` | (`list_name`, `feed_url`) | `updated_at` | |
| `podcast_settings` | (`user_id`, `feed_url`) | `updated_at` | |
| `episode_settings` | (`user_id`, `episode_url`) | `updated_at` | |

### Security constraints

**Decision**: importar/apagar/exportar sempre no escopo do usuário logado:
- ignorar qualquer item no arquivo cujo `user_id` não corresponda ao usuário atual
- quando a chave natural não inclui `user_id` (tabelas globais), permitir apenas
  inserir/atualizar registros necessários para as referências do próprio usuário
  (feeds/episodes referenciados por devices/lists/actions do usuário).

### Destructive actions confirmation

**Decision**: botões “Deletar dados” e “Deletar usuário” exigem confirmação
explícita no formulário (ex.: checkbox “confirm” ou input com frase).

## Alternatives considered

- Exportar “dump” bruto com IDs internos: rejeitado (não portável entre instâncias).
- Importar sobrescrevendo sempre: rejeitado (risco de perder dados mais novos).
