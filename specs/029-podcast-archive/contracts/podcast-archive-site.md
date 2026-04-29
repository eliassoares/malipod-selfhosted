# Contract: Podcast Archive Site Routes

**Feature**: `specs/029-podcast-archive/spec.md`

## POST `/podcast/{id}/archive`

Behavior:
- Requer usuário autenticado.
- Ativa o arquivamento do podcast.
- Enfileira (ou marca como queued) episódios do podcast ainda não arquivados.
- Redireciona para `GET /podcast/{id}`.

## DELETE `/podcast/{id}/archive`

Behavior:
- Requer usuário autenticado.
- Desativa o arquivamento do podcast.
- Cancela episódios em fila.
- Remove arquivos já baixados com segurança.
- Reseta estado de archive em episódios para “não arquivado”.
- Redireciona para `GET /podcast/{id}`.
