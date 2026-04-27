# Contract: Archive Status UI (Podcast page)

**Feature**: `specs/029-podcast-archive/spec.md`

On `GET /podcast/{id}`:
- Show a primary button when `archive=false`: “Baixar todos os episódios”.
- Show a destructive button when `archive=true`: “Cancelar arquivamento” (confirmation required).
- Each episode row shows one of:
  - `none`: no badge
  - `queued`: “Na fila”
  - `downloading`: “Baixando…”
  - `done`: badge + link to local file
  - `error`: badge + tooltip/message
