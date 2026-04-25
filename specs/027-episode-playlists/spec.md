# Feature Specification: Episode Playlists

**Feature Branch**: `027-episode-playlists`
**Created**: 2026-04-25
**Status**: Draft
**Input**: User description: "Implementar playlists de episódios com páginas de gerenciamento e detalhes, favoritos como playlist especial, adicionar episódio a playlists via popup, e incluir playlists no export/import do usuário."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Gerenciar playlists (Priority: P1)

Como usuário autenticado, eu quero criar, editar e apagar playlists de episódios
para organizar o que vou ouvir, e depois adicionar episódios à playlist por
busca.

**Why this priority**: Sem CRUD de playlists não existe valor de “playlists” no
produto; é a base para os demais fluxos.

**Independent Test**: Pode ser testado criando uma playlist via modal, validando
restrições (nome, descrição, imagem), e confirmando que ela aparece na listagem.

**Acceptance Scenarios**:

1. **Given** que o usuário está logado, **When** abre o modal de criação e envia
   nome/descrição/imagem válidos, **Then** a playlist é criada e passa a aparecer
   na página de gerenciamento.
2. **Given** que a playlist existe, **When** o usuário edita nome/descrição/imagem,
   **Then** as alterações são persistidas e refletidas na UI.
3. **Given** que a playlist existe e não é “Favoritos”, **When** o usuário clica
   em apagar e confirma no modal de confirmação irreversível, **Then** a playlist
   é removida e não aparece mais.
4. **Given** que a playlist “Favoritos” está listada, **When** o usuário tenta
   editar ou apagar, **Then** a UI indica que a playlist não pode ser editada e
   a ação não é permitida.

---

### User Story 2 - Visualizar detalhes e métricas da playlist (Priority: P2)

Como usuário, eu quero abrir uma playlist e ver seus episódios e métricas
principais (ex.: quantos episódios, tempos e data de criação), para entender o
progresso do que eu planejei ouvir.

**Why this priority**: Depois de criar playlists, o usuário precisa consumi-las;
as métricas tornam a playlist útil e “monitorável”.

**Independent Test**: Pode ser testado criando uma playlist com episódios e
verificando que a página de detalhes exibe métricas e lista de episódios.

**Acceptance Scenarios**:

1. **Given** que o usuário possui playlists, **When** abre a página de detalhes
   de uma playlist, **Then** vê imagem (ou placeholder), nome, descrição, data
   de criação, total de episódios, tempo ouvido e tempo total.
2. **Given** que o usuário não escolheu imagem para a playlist, **When** abre a
   playlist, **Then** uma imagem de placeholder (Malte/Lilith) é exibida.

---

### User Story 3 - Adicionar episódio a playlists (Priority: P3)

Como usuário, eu quero adicionar um episódio a uma ou mais playlists diretamente
na página do episódio (sem sair do contexto), para organizar rapidamente.

**Why this priority**: Reduz atrito no principal momento de ação (quando o usuário
está vendo um episódio).

**Independent Test**: Pode ser testado abrindo um episódio, acionando “Adicionar
à playlist”, selecionando múltiplas playlists e verificando que o episódio passa
a constar nelas.

**Acceptance Scenarios**:

1. **Given** que o usuário está logado e existem playlists, **When** abre um
   episódio e usa o popup “Adicionar à playlist”, **Then** consegue selecionar
   mais de uma playlist e confirmar a adição.
2. **Given** que o episódio já está em uma playlist, **When** tenta adicionar de
   novo à mesma playlist, **Then** o sistema evita duplicidade e não cria entradas
   repetidas.

---

### Edge Cases

- O que acontece quando a descrição excede 1024 caracteres?
- O que acontece quando a imagem enviada excede 1MB ou é um tipo inválido?
- O que acontece quando o usuário tenta acessar/editar/apagar playlists de outro usuário?
- O que acontece quando um episódio listado em uma playlist deixa de existir ou
  fica indisponível?
- O que acontece quando não existem playlists além de “Favoritos”?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST oferecer uma página para gerenciar playlists do usuário
  (listar, criar, editar e apagar).
- **FR-002**: Criação/edição de playlist MUST aceitar `nome` e `descrição` com
  limite de 1024 caracteres.
- **FR-003**: Criação/edição de playlist MUST permitir upload opcional de imagem
  com limite de 1MB.
- **FR-004**: Ao criar uma playlist, o usuário MUST poder pesquisar episódios e
  adicionar/remover episódios da playlist.
- **FR-005**: Deleção MUST exigir confirmação explícita em um popup/modal e MUST
  comunicar que é irreversível.
- **FR-006**: O sistema MUST exibir “Favoritos” como uma playlist especial na
  listagem de playlists.
- **FR-007**: A playlist “Favoritos” MUST ser somente leitura (não editável e não
  removível) e MUST permanecer compatível com o comportamento de sincronização já
  existente para favoritos.
- **FR-008**: Quando uma playlist (incluindo “Favoritos”) não tiver imagem definida,
  o sistema MUST exibir uma imagem placeholder escolhida aleatoriamente entre as
  opções disponíveis (Malte/Lilith).
- **FR-009**: O sistema MUST disponibilizar um botão “Adicionar à playlist” na
  página de detalhes do episódio, abrindo um popup com todas as playlists do usuário.
- **FR-010**: O popup “Adicionar à playlist” MUST permitir selecionar múltiplas
  playlists e adicionar o episódio a todas as selecionadas em uma única ação.
- **FR-011**: O sistema MUST impedir duplicidade de um mesmo episódio na mesma playlist.
- **FR-012**: O usuário MUST ver, na página de detalhes de uma playlist, métricas
  e informações: total de episódios, data de criação, tempo ouvido, tempo total e imagem.
- **FR-013**: Playlists e suas associações com episódios MUST ser incluídas no
  export/import de dados do usuário junto com as demais tabelas/entidades já suportadas.
- **FR-014**: Todas as páginas e ações de playlists MUST ser restritas ao dono do
  conteúdo (isolamento entre contas).

### Non-Functional Requirements *(mandatory)*

- **NFR-001**: Evidência de verificação MUST incluir testes automatizados cobrindo:
  criação/edição/deleção de playlists, inclusão de “Favoritos” como playlist especial,
  e adicionar episódio a playlists via página do episódio.
- **NFR-002**: O sistema MUST validar entradas e limites (descrição 1024, imagem 1MB)
  e MUST tratar erros com mensagens compreensíveis ao usuário.
- **NFR-003**: Qualquer mudança MUST manter compatibilidade com o que já existe
  (especialmente favoritos e export/import), evitando regressões.

### Key Entities *(include if feature involves data)*

- **Playlist**: Coleção de episódios com nome, descrição, imagem opcional, data de criação e métricas agregadas.
- **Playlist Membership**: Relação que conecta episódios a playlists (um episódio pode estar em várias playlists).
- **Favorites Playlist**: Playlist especial representando os episódios favoritos já existentes; não editável.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Um usuário consegue criar uma playlist válida (nome/descrição/imagem opcional)
  e vê-la listada em até 30 segundos sem erros.
- **SC-002**: O sistema bloqueia 100% das tentativas de salvar descrição > 1024 caracteres
  e de upload de imagem > 1MB, com feedback claro ao usuário.
- **SC-003**: O usuário consegue adicionar um episódio a 2+ playlists a partir da
  página do episódio em uma única ação (sem recarregar a página mais de uma vez).
- **SC-004**: Export/import do usuário preserva playlists e membros de playlists,
  e a reimportação permite reconstruir o estado (com “Favoritos” permanecendo compatível).

## Assumptions

- Usuários já possuem autenticação e sessão ativa para acessar páginas de playlists.
- Episódios já existem no sistema com identificadores estáveis e páginas de detalhes.
- “Tempo ouvido” e “progresso” são derivados de dados de escuta já existentes no produto.
- As imagens placeholder Malte/Lilith já existem como recursos visuais disponíveis para a UI.
- A listagem de episódios dentro de uma playlist não requer ordenação manual no MVP;
  a ordem padrão é suficiente para v1.

## Constitution Alignment *(mandatory)*

- **Slice Integrity**: US1 entrega um MVP útil (playlists criáveis e gerenciáveis).
  US2 adiciona consumo/valor (detalhes + métricas). US3 reduz atrito (adicionar via episódio).
- **Branch Plan**: Implementação ocorrerá na branch `027-episode-playlists`, criada a partir de `main`.
- **Verification Plan**: `uv run pytest`, `uv run ruff check .`, `uv run mypy .`,
  `uv run bandit -r app -c pyproject.toml`, `uv run pip-audit`.
- **Quality Gate Strategy**: Resolver avisos na raiz; sem `# noqa`/`# nosec` como atalho.
- **Review Readiness**: O PR deve resumir páginas adicionadas, comportamento de “Favoritos”
  como playlist especial, validações (1024/1MB), e evidência de testes/gates.
- **Security/Simplicity Notes**: Principal risco é acesso indevido entre contas e upload
  de arquivo; validações e restrições de permissão são obrigatórias.
