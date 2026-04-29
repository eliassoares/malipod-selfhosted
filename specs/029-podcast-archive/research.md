# Research: Podcast Archive

**Date**: 2026-04-25
**Feature**: `specs/029-podcast-archive/spec.md`

## Decision 1: Scheduler periódico (sem nova dependência)

**Decision**: Implementar a sincronização periódica com um loop asyncio (`asyncio.create_task` + `asyncio.sleep`) inicializado no lifespan.

**Rationale**:
- Mantém o projeto simples e evita adicionar dependências (princípio de simplicidade).
- A necessidade atual é um job único e recorrente (a cada N minutos), sem calendário complexo.

**Alternatives considered**:
- APScheduler: mais recursos, mas adiciona dependência e complexidade de lifecycle.

## Decision 2: Fila de download e workers

**Decision**: Usar `asyncio.Queue[int]` (episode_id) e N workers assíncronos controlados por `ARCHIVE_WORKERS`.

**Rationale**:
- Fácil de controlar concorrência.
- Não bloqueia requests e permite idempotência por episódio.

**Alternatives considered**:
- Celery/RQ: pesado para o escopo atual.
- BackgroundTasks do FastAPI: adequado para tarefas curtas, não para workers contínuos.

## Decision 3: Idempotência e controle de estados

**Decision**: `enqueue_episode()` verifica e só transita `archive_status` de `none` → `queued` quando apropriado; o worker revalida estado antes de baixar.

**Rationale**:
- Evita duplicação na fila e em disco.
- Garante convergência mesmo com requests repetidas e cron recorrente.

**Alternatives considered**:
- Deduplicação apenas em memória: perde robustez ao reiniciar o processo.

## Decision 4: Segurança de paths

**Decision**: Persistir no banco um `archive_path` relativo, sempre gerado pelo sistema, e ao remover arquivos garantir que o path final resolvido permanece dentro do `ARCHIVE_DIR`.

**Rationale**:
- Previne path traversal e remoção acidental fora do diretório de archive.

## Decision 5: Slugs e colisões

**Decision**: Gerar `podcast_slug` e `episode_slug` com slugify e acrescentar um sufixo curto derivado de um identificador estável do episódio (ex.: hash/trunc do `episode_url`).

**Rationale**:
- Minimiza colisões de nomes e mantém paths legíveis.
