# Feature Specification: Podcast Archive

**Feature Branch**: `029-podcast-archive`
**Created**: 2026-04-25
**Status**: Draft
**Input**: User description: "Permitir que o usuário archive um podcast para baixar automaticamente todos os episódios e manter o arquivo sincronizado. Ao desativar, apagar os arquivos."

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.

  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Ativar arquivamento de um podcast (Priority: P1)

Como usuário, quero marcar um podcast como “arquivado”, para que todos os episódios desse podcast sejam baixados e mantidos disponíveis localmente.

**Why this priority**: É o núcleo do valor: permitir que o usuário tenha uma cópia local e contínua do conteúdo de um podcast.

**Independent Test**: Arquivar um podcast e verificar que os episódios entram em fila/andamento/concluídos e que arquivos locais são criados.

**Acceptance Scenarios**:

1. **Given** um podcast com episódios e arquivamento desativado, **When** o usuário ativa o arquivamento, **Then** o sistema agenda o download de todos os episódios pendentes desse podcast.
2. **Given** que o arquivamento foi ativado, **When** o usuário acessa a página do podcast, **Then** ele vê o estado de arquivamento e o status de download por episódio.

---

### User Story 2 - Manter o arquivo sincronizado (Priority: P2)

Como usuário, quero que o arquivamento continue trazendo automaticamente episódios novos, para manter o podcast local sempre atualizado.

**Why this priority**: Sem sincronização, o arquivamento vira um “snapshot” e perde a principal utilidade no uso contínuo.

**Independent Test**: Com o arquivamento ativo, criar um novo episódio no feed (ou simular entrada) e verificar que ele é agendado e baixado sem ação manual do usuário.

**Acceptance Scenarios**:

1. **Given** um podcast arquivado e um episódio novo detectado, **When** a sincronização periódica roda, **Then** o episódio novo é adicionado ao fluxo de download.
2. **Given** um episódio já baixado, **When** a sincronização periódica roda novamente, **Then** ele não é baixado novamente.

---

### User Story 3 - Desativar e limpar arquivamento (Priority: P3)

Como usuário, quero desativar o arquivamento de um podcast, para cancelar itens ainda pendentes e apagar os arquivos já baixados com segurança.

**Why this priority**: Dá controle ao usuário e evita consumo de disco desnecessário. Também reduz risco de armazenamento “esquecido”.

**Independent Test**: Desativar o arquivamento e verificar que: downloads pendentes são desmarcados e arquivos existentes são apagados.

**Acceptance Scenarios**:

1. **Given** um podcast arquivado com episódios em fila e concluídos, **When** o usuário desativa o arquivamento e confirma a ação destrutiva, **Then** itens em fila são cancelados e arquivos concluídos são removidos.
2. **Given** que o arquivamento foi desativado, **When** o usuário volta à página do podcast, **Then** o estado volta a “não arquivado” e os episódios aparecem como “não arquivados”.

---

[Add more user stories as needed, each with an assigned priority]

### Edge Cases

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right edge cases.
-->

- O que acontece se um episódio não tiver URL de mídia disponível? (o status deve ir para erro e mostrar uma mensagem)
- O que acontece se o download falhar por rede, timeout ou erro de escrita em disco? (registrar erro e permitir reprocessamento)
- O que acontece se o usuário desativar arquivamento durante um download? (não deve corromper arquivos; deve convergir para “desativado e limpo”)
- O que acontece se o mesmo episódio for agendado duas vezes? (deve ser idempotente e não duplicar)

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: O sistema MUST permitir que o usuário ative o arquivamento para um podcast.
- **FR-002**: Ao ativar o arquivamento, o sistema MUST agendar o download de todos os episódios ainda não arquivados daquele podcast.
- **FR-003**: O sistema MUST baixar episódios e gravar os arquivos em um diretório de arquivo local do servidor.
- **FR-004**: O sistema MUST manter o arquivamento sincronizado periodicamente, agendando downloads de episódios novos para podcasts arquivados.
- **FR-005**: O sistema MUST permitir que o usuário desative o arquivamento, cancelando itens pendentes e apagando os arquivos já baixados.
- **FR-006**: O sistema MUST exibir na página do podcast um indicador de status do arquivamento e o status por episódio (pendente, em fila, baixando, concluído, erro).
- **FR-007**: O sistema MUST registrar mensagens de erro por episódio quando o download falhar, de modo que o usuário entenda o motivo.
- **FR-008**: O sistema MUST ser idempotente: agendar o mesmo episódio mais de uma vez não deve gerar duplicação ou corrupção.
- **FR-009**: O sistema MUST restringir as ações de arquivamento a usuários autenticados e apenas para podcasts acessíveis pelo usuário (sem permitir ativar/desativar em nome de terceiros).

*Example of marking unclear requirements:*

<!-- No clarifications needed for this spec. -->

### Non-Functional Requirements *(mandatory)*

- **NFR-001**: Evidência de verificação MUST incluir testes automatizados para:
  - ativar/desativar arquivamento e transições de status por episódio;
  - idempotência de enfileiramento;
  - limpeza de arquivos ao desativar arquivamento (sem apagar fora do diretório de arquivo).
- **NFR-002**: O sistema MUST validar entradas e caminhos de arquivo para evitar escrita/leitura fora do diretório de arquivo configurado.
- **NFR-003**: O sistema MUST limitar concorrência e uso de recursos para não degradar o site (ex.: downloads em paralelo controlados).

### Key Entities *(include if feature involves data)*

- **Podcast Archive Flag**: indica se um podcast está marcado para arquivamento.
- **Episode Archive State**: estado do arquivamento por episódio (não arquivado, em fila, baixando, concluído, erro) e referência ao arquivo local quando concluído.
- **Archive Storage**: diretório local de arquivo onde os episódios são gravados e removidos.

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: Usuários conseguem ativar o arquivamento de um podcast e ver episódios entrando em fila em menos de 5 segundos após a ação.
- **SC-002**: Para um podcast com 100 episódios, o sistema consegue agendar 100 downloads sem duplicação de itens.
- **SC-003**: Ao desativar o arquivamento, o sistema remove os arquivos baixados daquele podcast e o usuário não vê mais itens como “concluídos” em até 30 segundos.
- **SC-004**: Episódios com falha de download aparecem com estado de erro e mensagem associada, permitindo diagnóstico sem acesso ao servidor.

## Assumptions

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right assumptions based on reasonable defaults
  chosen when the feature description did not specify certain details.
-->

- O usuário está autenticado para ativar/desativar arquivamento.
- O servidor tem acesso a armazenamento local persistente e permissões de escrita no diretório de arquivo.
- Alguns episódios podem não ter mídia disponível; estes devem falhar de forma controlada.
- O arquivamento é por podcast (não por episódio individual) nesta fase.

## Constitution Alignment *(mandatory)*

- **Slice Integrity**: Explain why each user story remains independently valuable
  and testable.
- **Branch Plan**: Confirm the feature will be implemented on a branch created
  from `main`.
- **Verification Plan**: List the checks that must pass before merge.
- **Quality Gate Strategy**: State how the feature will resolve lint, typing, and
  security findings without relying on `# noqa`, `# nosec`, or similar inline
  suppressions as shortcuts.
- **Review Readiness**: State what the final pull request must summarize for this
  feature.
- **Security/Simplicity Notes**: Record any notable risk, dependency, or complexity
  decision that planning must justify.

- **Slice Integrity**: US1 entrega o fluxo de arquivar (valor imediato). US2 adiciona atualização contínua sem quebrar US1. US3 adiciona controle e limpeza (valor incremental) e é testável isoladamente.
- **Branch Plan**: Implementação ocorrerá no branch `029-podcast-archive`, criado a partir de `main`.
- **Verification Plan**: Antes do merge, devem passar `uv run pytest`, `uv run ruff check .`, `uv run ruff format .`, `uv run mypy app/ tests/`, `uv run bandit -r app -c pyproject.toml` e auditoria de dependências conforme padrão do repo.
- **Quality Gate Strategy**: Resolver achados de lint/tipos/segurança na causa raiz (sem suprimir avisos como atalho).
- **Review Readiness**: O PR deve resumir: UX de ativar/desativar, estados por episódio, sincronização periódica, idempotência e política de limpeza em disco.
- **Security/Simplicity Notes**: Risco principal é manipulação de caminhos e remoção de arquivos; planejamento deve justificar a estratégia para garantir que operações fiquem confinadas ao diretório de arquivo e sejam owner-only.
