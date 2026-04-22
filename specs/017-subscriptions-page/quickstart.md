# Quickstart: Subscriptions Page

## Run

```bash
uv run uvicorn app.main:app --reload
```

## Try

1. Register: `http://localhost:8000/register`
2. Login: `http://localhost:8000/login`
3. Open subscriptions page: `http://localhost:8000/user/subscriptions/<your-nickname>`

## Validate

1. Deslogado: acessar `/user/subscriptions/<nickname>` deve redirecionar para `/login`.
2. Logado: página renderiza sem overflow em mobile.
3. Lista mostra: nome + imagem (ou placeholder) + contagem de episódios + “último episódio”.
4. Alternar lista/grid e recarregar mantém a preferência.
5. Ordenar por “mais recentes” e “mais antigos” altera a ordem.
6. Buscar filtra itens pelo nome.
7. Exportar OPML baixa um XML válido contendo os feeds seguidos.
