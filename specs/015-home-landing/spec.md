# Feature Specification: Home Landing Page

**Feature Branch**: `015-home-landing`
**Created**: 2026-04-20
**Status**: Draft
**Input**: User description: "adicionei um novo arquivo em google_stitch_templates/landing_page_malipod_next, é para se basear nele, e nao utilizar do jeito que está, gostaria que alterasse o arquivo html para: - Onde tiver gpoddernext, alterar para Malipod - Alterar a descrição e o texto para ser condizente com o que o site faz - Que tenha, visualmente, o mesmo padrão das demais páginas - Que seja mobile friedly Essa página será a nova página inicial, a página de home. Se o usuário tiver logado, o botão de logout deve ficar disponivel e o de criar conta e logar nao visivel, se o usuário tiver deslogado, o botar de logar ou criar conta fica visivel e o de deslogar nao fica visivel"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Landing page clara para visitantes (Priority: P1)

Como visitante (sem estar logado), eu quero acessar a página inicial do Malipod e
entender rapidamente o que o serviço faz, com chamadas para ação claras para
criar conta e fazer login.

**Why this priority**: É a primeira impressão do produto e o caminho principal
para aquisição de usuários.

**Independent Test**: Pode ser testado acessando `/` sem cookies de sessão e
verificando que o conteúdo e os botões de CTA exibidos são “Criar conta” e
“Entrar”, e que não existe opção de “Sair”.

**Acceptance Scenarios**:

1. **Given** um visitante sem sessão ativa, **When** acessa `GET /`, **Then** a
   página exibe o nome “Malipod” e texto descritivo condizente com o serviço.
2. **Given** um visitante sem sessão ativa, **When** acessa `GET /`, **Then** a
   página exibe botões/links para “Criar conta” e “Entrar” e NÃO exibe “Sair”.

---

### User Story 2 - Landing page com ações para usuários logados (Priority: P2)

Como usuário autenticado, eu quero que a página inicial apresente ações
compatíveis com meu estado logado, incluindo opção de sair, e não incentive login/cadastro.

**Why this priority**: Evita fricção e reduz confusão para usuários já autenticados.

**Independent Test**: Pode ser testado acessando `/` com cookie de sessão válido
e verificando que “Sair” está disponível e “Criar conta/Entrar” não aparecem.

**Acceptance Scenarios**:

1. **Given** um usuário com sessão ativa, **When** acessa `GET /`, **Then** a
   página exibe um botão/ação de “Sair”.
2. **Given** um usuário com sessão ativa, **When** acessa `GET /`, **Then** a
   página NÃO exibe botões/links de “Criar conta” e “Entrar”.

---

### User Story 3 - Experiência mobile-friendly e consistente (Priority: P3)

Como usuário em um dispositivo móvel, eu quero que a página inicial seja
legível, navegável e visualmente consistente com as demais páginas do site.

**Why this priority**: A maioria dos usuários acessa pelo celular; consistência
visual reduz estranhamento e aumenta confiança.

**Independent Test**: Pode ser testado em viewport pequeno (mobile) verificando
que não há overflow horizontal e que os CTAs permanecem acessíveis.

**Acceptance Scenarios**:

1. **Given** viewport mobile, **When** acessa `GET /`, **Then** o layout se
   adapta sem exigir zoom e sem rolagem horizontal.
2. **Given** o site com header/footer padrão, **When** acessa `GET /`, **Then** a
   página mantém o mesmo padrão visual e de componentes das demais páginas.

---

### Edge Cases

- A página inicial não deve conter a marca antiga (“gpoddernext” / “Gpodder Next”).
- O conteúdo deve permanecer utilizável mesmo sem JavaScript (exceto menu mobile).
- Em ambiente não pronto (dependências indisponíveis), a página ainda deve ser
  exibida com indicação apropriada de indisponibilidade (sem quebra do layout).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST usar a nova landing page como página inicial em `GET /`.
- **FR-002**: O conteúdo da landing page MUST usar a marca “Malipod” (sem menções a “gpoddernext”).
- **FR-003**: Para visitantes deslogados, a página MUST exibir CTAs para “Criar conta” e “Entrar” e MUST NOT exibir CTA de “Sair”.
- **FR-004**: Para usuários logados, a página MUST exibir CTA de “Sair” e MUST NOT exibir CTAs de “Criar conta” e “Entrar”.
- **FR-005**: O texto descritivo MUST ser condizente com o propósito do Malipod (sincronização de podcasts e serviços relacionados).
- **FR-006**: A página MUST manter o padrão visual (tipografia, cores, layout base, header/footer) usado nas demais páginas do site.

### Non-Functional Requirements *(mandatory)*

- **NFR-001**: Evidências de verificação MUST incluir:
  - teste automatizado para `GET /` deslogado (conteúdo e CTAs corretos)
  - teste automatizado para `GET /` logado (CTAs corretos)
  - validação responsiva básica (inspeção manual em viewport mobile)
  - `uv run pytest` e `uv run ruff check .` passando
- **NFR-002**: A página MUST ser mobile-friendly (sem overflow horizontal e com CTAs acessíveis em telas pequenas).
- **NFR-003**: A mudança MUST reutilizar o sistema de autenticação e sessão existente; não introduzir novos métodos de login.

### Key Entities *(include if feature involves data)*

- **Session**: representa o estado autenticado (cookie de sessão) que determina quais CTAs ficam visíveis.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Visitantes deslogados encontram “Criar conta” e “Entrar” na página inicial em 100% dos testes automatizados.
- **SC-002**: Usuários logados veem “Sair” e não veem “Criar conta/Entrar” em 100% dos testes automatizados.
- **SC-003**: A página inicial não contém “gpoddernext” em 100% das verificações automatizadas.
- **SC-004**: A página inicial permanece utilizável em viewport mobile sem rolagem horizontal durante validação manual.

## Assumptions

- O site já possui rotas de cadastro (`/register`), login (`/login`) e logout (`/logout`).
- O padrão visual existente do site (base, header e footer) deve ser preservado.
- O conteúdo pode ser atualizado prioritariamente em pt-BR, mantendo os elementos
  de navegação existentes para outros idiomas.

## Constitution Alignment *(mandatory)*

- **Slice Integrity**: P1 entrega valor completo para visitantes; P2 adapta para
  usuários logados; P3 melhora UX sem mudar o contrato de navegação.
- **Branch Plan**: Implementação no branch `015-home-landing`, criado a partir de `main`.
- **Verification Plan**: Rodar `uv run pytest` e `uv run ruff check .`; validar
  manualmente em mobile (viewport estreito).
- **Quality Gate Strategy**: Corrigir lint/typing na raiz; sem `# noqa`/`# nosec`.
- **Review Readiness**: PR deve resumir mudanças no HTML/copy, comportamento
  logado vs deslogado e evidências de verificação.
- **Security/Simplicity Notes**: Mudança é apenas de apresentação; não altera
  regras de autenticação, apenas visibilidade de CTAs.
