# Quickstart: Home Landing Page

## Run

```bash
uv run uvicorn app.main:app --reload
```

## Try

- Visit home (unauthenticated): `http://localhost:8000/`
- Register: `http://localhost:8000/register`
- Login: `http://localhost:8000/login`

## Validate

1. Deslogado: ver CTAs “Criar conta” e “Entrar” (e não ver “Sair”).
2. Logado: ver “Sair” (e não ver “Criar conta/Entrar”).
3. Não encontrar texto “gpoddernext”.
4. Em viewport mobile, não haver rolagem horizontal.
