# Data Model: Web Audio Player Bar

**Date**: 2026-04-25
**Feature**: `specs/028-web-audio-player/spec.md`

## Database Changes

### 1) Persistência do último episódio no usuário

Adicionar colunas nullable em `users`:

- `last_episode_id` (referência ao episódio)
- `last_position_sec` (inteiro; posição atual em segundos)
- `last_queue_mode` (string curta; valores esperados: `playlist`, `podcast`)
- `last_queue_ref_id` (inteiro; `playlist_id` ou `podcast_id`)

Regras:
- Todas as colunas são opcionais.
- Se `last_episode_id` for removido, o estado do player volta para “inativo”.

### 2) Ordem determinística da fila em playlists

Adicionar coluna `position` em `episode_playlist_items` para permitir:
- ordenar a fila para reprodução (player)
- compatibilidade futura com reordenação

Backfill:
- preencher `position` na ordem atual de `created_at ASC` dentro de cada playlist.

## Derived/Serialized State

### Template injection

Em páginas autenticadas, injetar no HTML (no `base.html`) uma estrutura JSON com:
- `episodeId`
- `positionSec`
- `queueMode`
- `queueRefId`

Quando não houver estado anterior: injetar `null`.

### Browser session storage

O browser mantém em `sessionStorage`:
- fila atual (`episode_ids`)
- índice atual
- modo (`playlist`/`podcast`)
- referência (`playlist_id`/`podcast_id`)
- `episodeId` atual e `positionSec` atual (para recuperação imediata entre reloads)

## Services / Ownership Rules

- Atualização do player state sempre pertence ao usuário da sessão.
- Ações do player sempre usam `device_id = "web-player"` (um por usuário).
- O endpoint de “próximo episódio” só retorna episódios do mesmo feed do episódio atual.
