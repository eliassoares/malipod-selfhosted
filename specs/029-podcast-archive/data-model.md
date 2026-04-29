# Data Model: Podcast Archive

**Date**: 2026-04-25
**Feature**: `specs/029-podcast-archive/spec.md`

## Entities / Fields

### PodcastFeed

Adicionar:
- `archive` (bool) — indica se o podcast está em modo de arquivamento.

### Episode

Adicionar:
- `archive_status` — estado do arquivo do episódio (`none`, `queued`, `downloading`, `done`, `error`).
- `archive_path` — caminho relativo dentro de `ARCHIVE_DIR` (ex.: `{podcast_slug}/{episode_slug}.mp3`).
- `archive_error` — mensagem de erro (quando `archive_status = error`).

## State Machine (Episode archive)

- `none` → `queued` (enfileirado)
- `queued` → `downloading` (worker iniciou)
- `downloading` → `done` (arquivo gravado e registrado)
- `downloading` → `error` (falha de download/escrita)
- `queued` → `none` (cancelado ao desativar podcast archive)
- `done` → `none` (removido ao desativar podcast archive + limpeza de arquivo)
- `error` → `queued` (opcional: reprocesso via sync; v1 pode manter em `error` e depender de ação futura)

## Storage Layout

- Diretório raiz configurável: `ARCHIVE_DIR` (default `./archive`).
- Estrutura em disco:
  - `{ARCHIVE_DIR}/{podcast_slug}/{episode_slug}.mp3`

Regras:
- `archive_path` é sempre relativo ao `ARCHIVE_DIR` e gerado pelo sistema.
- Remoção de arquivos deve validar confinamento ao diretório de archive.
