# Quickstart: User Data Tools

## Run

```bash
uv run uvicorn app.main:app --reload
```

## Try

1. Crie usuário em `/register` e faça login em `/login`.
2. Abra perfil: `/user/profile/<nickname>`.
3. Exportar: baixar `malipod_data_YYYY-MM-DD.json`.
4. Importar: enviar o arquivo exportado e verificar que não sobrescreve dados mais novos.
5. Deletar dados: confirmar e verificar que dados associados somem, mantendo `users`.
6. Deletar usuário: confirmar e verificar redirect para `/` e sessão encerrada.

## Verify

- `uv run pytest`
- `uv run ruff check .`
