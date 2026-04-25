# Contract: Player State Injection

**Feature**: `specs/028-web-audio-player/spec.md`

## `window.__PLAYER_STATE__`

Em qualquer página autenticada (renderizada com `base.html`), o servidor injeta:

```js
window.__PLAYER_STATE__ = null;
```

ou:

```js
window.__PLAYER_STATE__ = {
  episodeId: 123,
  positionSec: 45,
  queueMode: "playlist",
  queueRefId: 9
};
```

Regras:
- O valor deve existir sempre (mesmo que `null`).
- Deve refletir as colunas atuais do usuário no banco.
- O JS do player deve inicializar em modo pausado a partir desse valor (quando presente).
