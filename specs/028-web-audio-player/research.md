# Research: Web Audio Player Bar

**Date**: 2026-04-25
**Feature**: `specs/028-web-audio-player/spec.md`

## Decision 1: Persistência do player entre páginas (sem SPA)

**Decision**: Usar o `<audio>` + estado do player no `base.html`, e persistir/restaurar o estado entre reloads via `sessionStorage`.

**Rationale**:
- O projeto é server-rendered; manter um DOM “imutável” entre navegações exigiria SPA.
- `sessionStorage` é suficiente para o escopo atual (persistência durante a sessão do navegador) e evita armazenamento permanente.

**Alternatives considered**:
- Service Worker/PWA (fora do escopo).
- SPA parcial (aumenta complexidade e risco de inconsistência com templates existentes).

## Decision 2: Persistência do “último episódio” no servidor

**Decision**: Persistir no usuário: `last_episode_id`, `last_position_sec`, `last_queue_mode`, `last_queue_ref_id` (nullable).

**Rationale**:
- Permite retomar quando o usuário abre qualquer página autenticada, sem depender do estado do browser.
- É compatível com métricas e histórico existentes.

**Alternatives considered**:
- Persistir apenas em browser storage (não permite retomada entre abas/dispositivos).

## Decision 3: Identidade de device do player web

**Decision**: Criar (idempotente) um `DeviceModel` por usuário com:
- `device_id = "web-player"`
- `device_type = "browser"`
- `caption = "MaliPod Web Player"`

**Rationale**:
- Permite que as ações do player entrem nas tabelas gpodder com device consistente.
- Mantém a separação de eventos entre dispositivos, sem interferir na sincronização normal.

**Alternatives considered**:
- Registrar eventos com `device_pk = NULL` (perde rastreabilidade por dispositivo).

## Decision 4: Registro de eventos gpodder (play/pause/conclusão)

**Decision**: Registrar eventos via o mesmo serviço que processa uploads da API de episódios (`EpisodeService.upload_actions`), garantindo atualização de `EpisodeActionModel` e inserção em `EpisodeActionEventModel`.

**Rationale**:
- Reuso de lógica e consistência com o protocolo.
- Reduz risco de divergência de cálculo de progresso/estado.

**Alternatives considered**:
- Inserção manual em tabelas (mais risco e duplicação).

## Decision 5: Ordem da fila em playlists

**Decision**: Garantir uma ordem determinística para fila de playlists.

**Rationale**:
- O player precisa de uma ordem estável para avançar ao próximo episódio.
- O código atual de playlists ordena itens por criação; a spec pede ordenação por “posição”.

**Alternatives considered**:
- Usar `created_at` como ordem (mais simples, mas não permite reordenar no futuro e não atende a definição de “posição”).

**Plan**:
- Adicionar uma coluna `position` em `episode_playlist_items` com backfill baseado em `created_at` (ordem existente).
- Ao adicionar um episódio, atribuir `position = max(position)+1`.

## Decision 6: Frequência de persistência do estado

**Decision**: Persistir estado no servidor:
- a cada 10 segundos de reprodução (throttle)
- ao pausar/parar

**Rationale**:
- Reduz perda de progresso sem gerar tráfego excessivo.

**Alternatives considered**:
- Persistir em todo `timeupdate` (demais).
- Persistência somente no unload (frágil).
