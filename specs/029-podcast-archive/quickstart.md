# Quickstart: Podcast Archive

**Feature**: `specs/029-podcast-archive/spec.md`
**Date**: 2026-04-25

## Local Setup (manual)

- Configure `ARCHIVE_DIR` (default `./archive`).
- Ensure docker-compose mounts `./archive:/app/archive` when running in containers.

## Manual Verification

1. Abra `GET /podcast/{id}` autenticado.
2. Clique “Baixar todos os episódios” e verifique que episódios entram em fila/baixando.
3. Verifique que arquivos aparecem no diretório `ARCHIVE_DIR`.
4. Aguarde a sincronização periódica e confirme que episódios novos são enfileirados.
5. Clique “Cancelar arquivamento” e confirme:
   - fila pendente é cancelada
   - arquivos são removidos do disco
   - status dos episódios volta a “não arquivado”.
