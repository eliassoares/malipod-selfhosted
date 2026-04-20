# Quickstart: Suggestions API

## Prerequisites

- Servidor rodando com `base_url` configurado
- Pelo menos dois usuários no banco e um podcast assinado por um deles
- Para testar sugestões: autenticar como um usuário que **não** assina o podcast popular

## Run

Executar o servidor (exemplo):

```bash
uv run uvicorn app.main:app --reload
```

## Try (Basic Auth)

JSON:

```bash
curl -u "<nickname>:<password>" "http://localhost:8000/suggestions/10.json"
```

OPML:

```bash
curl -u "<nickname>:<password>" "http://localhost:8000/suggestions/10.opml"
```

TXT:

```bash
curl -u "<nickname>:<password>" "http://localhost:8000/suggestions/10.txt"
```

## Verify behaviors

- Sem auth → `401 Unauthorized`
- `number` fora de `1..100` → `400 Bad Request`
- Podcasts já assinados pelo usuário autenticado não aparecem na lista
- Ordenação: mais `subscribers` primeiro (desempate por URL do feed)
