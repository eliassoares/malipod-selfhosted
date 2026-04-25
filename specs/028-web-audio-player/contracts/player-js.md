# Contract: `MaliPlayer` (browser)

**Feature**: `specs/028-web-audio-player/spec.md`
**File**: `app/static/js/player.js`

## Global API

- `MaliPlayer.load(episodeId, startSec)` → carrega episódio e prepara o player (estado pausado).
- `MaliPlayer.play()` / `MaliPlayer.pause()` → controles básicos.
- `MaliPlayer.seek(sec)` → altera posição do áudio.
- `MaliPlayer.next()` → avança na fila.
- `MaliPlayer.setQueue(ids, mode, refId)` → define fila e inicia no primeiro item.

## Events

- Atualiza UI em `timeupdate`.
- Emite persistência do estado (throttle ~10s) para `/web/player/state`.
- Emite ações do player para `/web/player/action` no `play`, `pause` e `ended`.

## Storage

- Usa `sessionStorage` para fila e retomada durante navegação.
