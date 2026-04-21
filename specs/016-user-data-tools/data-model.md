# Data Model: User Data Tools

**Feature**: `016-user-data-tools` | **Date**: 2026-04-20

## Scope

Sem novas tabelas. A feature opera sobre tabelas existentes via export/import/cleanup.

## Entities

### User Data Snapshot (JSON)

- Representa um conjunto de dados exportados de uma conta, particionados por tabela.
- Cada tabela é um campo no JSON (ex.: `"users"`, `"devices"`, `"podcast_feeds"`).
- Campos sensíveis (`password_hash`, `password_salt`) não aparecem no snapshot.

### User

- Fonte: `app/db/models/user.py::UserModel`
- Import/export: chave natural preferida `email` (fallback `nickname`), recência `updated_at`.

### Device

- Fonte: `app/db/models/device.py::DeviceModel`
- Import/export: chave natural (`user_id`, `device_id`), recência `updated_at`.

### Catalog (global)

- `podcast_feeds` (chave `feed_url`, recência `updated_at`)
- `episodes` (chave `episode_url`, recência `updated_at`)

## Relationships (high level)

- `users` 1:N `devices`
- `devices` relaciona com subscriptions e events por `device_pk`
- várias tabelas do usuário referenciam feeds/episodes por IDs internos, mas a exportação/importação usa URLs como chaves naturais
