# Contract: Suggestions API

## Endpoint

`GET /suggestions/{number}.{format}`

- `{number}`: inteiro `1..100` (fora do intervalo → `400`)
- `{format}`: `json` | `opml` | `txt` (inválido → `400`)
- Autenticação: obrigatória (cookie de sessão **ou** Basic Auth)

## Responses

### 200 OK (JSON)

`Content-Type: application/json`

Body: array de objetos com:

- `url`: string (feed URL)
- `title`: string
- `author`: string | null
- `description`: string | null
- `subscribers`: integer (>= 1)
- `logo_url`: string | null
- `website`: string | null
- `mygpo_link`: string (URL construída a partir do `base_url` do servidor)

### 200 OK (OPML)

`Content-Type: application/xml`

Body: OPML 1.0 com `outline` por podcast, com `xmlUrl` apontando para o feed.

### 200 OK (TXT)

`Content-Type: text/plain; charset=utf-8`

Body: uma URL de feed por linha.

### 400 Bad Request

- `number` fora de `1..100`
- `format` diferente de `json|opml|txt`

Body: JSON de erro FastAPI/Starlette padrão (`detail: ...`).

### 401 Unauthorized

Sem credenciais válidas (sem cookie válido e sem Basic Auth válido).

- Deve incluir header `WWW-Authenticate: Basic` (para compatibilidade com clientes).

## Notes

- Read-only: nenhuma escrita no banco.
- Nunca inclui feeds já assinados pelo usuário autenticado.
- Quando não houver sugestões elegíveis, retorna `200` com lista vazia (JSON) / documento vazio compatível (OPML/TXT).
