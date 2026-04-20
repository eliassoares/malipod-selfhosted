# Research: Home Landing Page

**Feature**: `015-home-landing` | **Date**: 2026-04-20

## Goal

Definir como integrar a nova landing page ao padrão atual do site (base/partials),
garantir CTAs por estado logado e manter responsividade sem criar dependências novas.

## Findings (codebase)

### Existing layout system

- `app/templates/base.html` inclui `partials/head.html`, `partials/topbar.html` e `partials/footer.html`.
- O topbar já é responsivo (menu mobile) e já alterna botões por `current_user`:
  - logado: mostra “Logout” (+ link perfil)
  - deslogado: mostra “Register” e “Login”

**Decision**: fazer `home.html` estender `base.html` e delegar navegação ao topbar.

### Auth state available on site pages

- `app/api/deps.py#get_current_user` resolve sessão via cookie.
- Páginas de auth (`app/api/routes/auth_site.py`) passam `current_user` e `copy` via `build_context(...)`.
- O handler atual de `/` (`app/api/routes/site.py`) não inclui `current_user`/`copy` no contexto, e usa um template antigo standalone.

**Decision**: atualizar `GET /` para resolver `current_user` e locale/copy (via `LocalizationService`)
e passar ao template o mesmo conjunto de variáveis do restante do site.

### Reference template

- Existe um HTML de referência em `google_stitch_templates/landing_page_malipod_next/code.html`.
- Ele já usa o mesmo conjunto de cores e fontes (Tailwind config semelhante ao `partials/head.html`),
mas não está integrado aos partials do projeto e contém cópia/brand antiga.

**Decision**: “basear” o layout/estrutura visual no template, mas reimplementar como Jinja template
sob `base.html`, reutilizando o topbar/footer do projeto e removendo dependências supérfluas
do HTML de referência.

## Decisions

- **Brand**: substituir todas as ocorrências “gpoddernext/Gpodder Next” por “Malipod”.
- **CTAs dentro da landing**:
  - deslogado: botões para `/register` e `/login`
  - logado: botão `POST /logout` e link para perfil
- **Mobile-friendly**: usar grid responsivo (1 coluna → 2/3 colunas) e tipografia/spacing adaptáveis;
evitar imagens grandes e garantir container com padding em telas pequenas.
