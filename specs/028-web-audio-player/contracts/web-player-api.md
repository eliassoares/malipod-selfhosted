# Contract: Web Player API

**Feature**: `specs/028-web-audio-player/spec.md`
**Scope**: Rotas JSON autenticadas sob `/web/*`

## Auth

- Todas as rotas exigem sessão válida (mesma regra de páginas do site).
- Se não autenticado: retornar `401`.

## POST `/web/player/state`

Salva o estado do player no usuário.

### Request (JSON)

```json
{
  "episode_id": 123,
  "position_sec": 45,
  "queue_mode": "playlist",
  "queue_ref_id": 9
}
```

Campos:
- `episode_id`: inteiro ou `null`
- `position_sec`: inteiro ou `null`
- `queue_mode`: `"playlist"` | `"podcast"` | `null`
- `queue_ref_id`: inteiro ou `null`

### Response (JSON)

```json
{
  "ok": true
}
```

## POST `/web/player/action`

Registra um evento do player e cria o device web do usuário se necessário.

### Request (JSON)

```json
{
  "episode_id": 123,
  "action": "play",
  "position": 45,
  "total": 1200,
  "started": 40
}
```

Campos:
- `episode_id`: inteiro (obrigatório)
- `action`: `"play"` | `"pause"` | `"stop"` (obrigatório)
- `position`: inteiro ou `null`
- `total`: inteiro ou `null`
- `started`: inteiro ou `null` (posição no início do play)

### Response (JSON)

```json
{
  "ok": true
}
```

## GET `/web/episode/{episode_id}/next`

Retorna o próximo episódio do mesmo podcast (modo podcast).

### Response (JSON)

```json
{
  "episode_id": 122
}
```

Quando não existe próximo episódio:

```json
{
  "episode_id": null
}
```
