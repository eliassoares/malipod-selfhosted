# Feature Specification: Device Synchronization API

**Feature Branch**: `011-device-sync-api`
**Created**: 2026-04-18
**Status**: Draft
**Input**: User description: "Vamos desenvolver a api Device Synchronization. Device Synchronization API: Get Sync Status (GET /api/2/sync-devices/(username).json) e Start/Stop Sync (POST /api/2/sync-devices/(username).json), requer autenticação, desde 2.10, com respostas de grupos sincronizados e não sincronizados."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consultar status de sincronização (Priority: P1)

Como usuário autenticado (via aplicativo cliente), eu quero consultar o status de sincronização entre meus dispositivos para entender quais dispositivos estão compartilhando o mesmo estado e quais estão isolados.

**Why this priority**: Sem visibilidade do status, o usuário não consegue diagnosticar problemas nem confirmar se a configuração entre dispositivos está correta.

**Independent Test**: Pode ser testado apenas consultando o status e validando que a resposta separa corretamente dispositivos em “sincronizados” (grupos) e “não sincronizados”.

**Acceptance Scenarios**:

1. **Given** um usuário autenticado com múltiplos dispositivos registrados, **When** o cliente solicita o status, **Then** a resposta lista pelo menos um grupo em `synchronized` e inclui os demais dispositivos em `not-synchronized` quando aplicável.
2. **Given** um usuário autenticado sem grupos de sincronização configurados, **When** o cliente solicita o status, **Then** `synchronized` é uma lista vazia e `not-synchronized` contém todos os dispositivos do usuário.

---

### User Story 2 - Iniciar e parar sincronização entre dispositivos (Priority: P2)

Como usuário autenticado (via aplicativo cliente), eu quero iniciar e parar sincronização entre dispositivos para controlar em quais dispositivos meu estado será compartilhado.

**Why this priority**: Permite que o usuário ajuste o comportamento conforme uso real (ex.: sincronizar notebook e netbook, mas manter um PC de trabalho separado).

**Independent Test**: Pode ser testado enviando uma solicitação de configuração e validando que a resposta de status reflete a mudança de agrupamento.

**Acceptance Scenarios**:

1. **Given** um usuário autenticado com pelo menos dois dispositivos “não sincronizados”, **When** o cliente solicita sincronizar esses dispositivos, **Then** eles passam a aparecer juntos no mesmo grupo em `synchronized`.
2. **Given** um usuário autenticado com um dispositivo participante de um grupo sincronizado, **When** o cliente solicita parar a sincronização desse dispositivo, **Then** esse dispositivo deixa o grupo e passa a aparecer em `not-synchronized`.

---

### User Story 3 - Segurança e mensagens de erro previsíveis (Priority: P3)

Como usuário autenticado, eu quero receber respostas previsíveis para erros comuns (entrada inválida, dispositivos inexistentes, acesso negado) para que o aplicativo possa orientar o usuário e evitar configurações incorretas.

**Why this priority**: Reduz frustração e suporte; garante que clientes diferentes tenham comportamento consistente.

**Independent Test**: Pode ser testado com entradas inválidas e tentativas de acesso a dados de outro usuário.

**Acceptance Scenarios**:

1. **Given** um usuário autenticado, **When** o cliente solicita alterar sincronização com um nome de dispositivo inexistente, **Then** a resposta indica erro de validação e não aplica alterações parciais.
2. **Given** um usuário autenticado, **When** o cliente tenta consultar/alterar o status de um `username` diferente do seu, **Then** o acesso é negado.

---

### Edge Cases

- Consultar status para um usuário sem dispositivos registrados deve retornar listas vazias (e não erro).
- A mesma string de dispositivo repetida na mesma solicitação não deve causar falha; deve ser tratada como duplicata e ignorada.
- Solicitar sincronização de dispositivos já sincronizados (mesmo grupo) deve ser idempotente (sem alterar o resultado final).
- Solicitar parar sincronização de um dispositivo já “não sincronizado” deve ser idempotente.
- Solicitar sincronização contendo dispositivos de usuários diferentes deve ser rejeitado com erro (sem alterações aplicadas).
- Solicitações sem autenticação devem ser rejeitadas.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST expor uma interface para consultar o status de sincronização de dispositivos por usuário em `GET /api/2/sync-devices/{username}.json`.
- **FR-002**: O sistema MUST exigir autenticação para consultar o status de sincronização.
- **FR-003**: O sistema MUST autorizar o acesso apenas ao próprio `username` do usuário autenticado (ou a perfis explicitamente autorizados por política administrativa existente).
- **FR-004**: O sistema MUST retornar o status no formato:
  - `synchronized`: lista de grupos, onde cada grupo é uma lista de nomes de dispositivos que estão mutuamente sincronizados
  - `not-synchronized`: lista de nomes de dispositivos que não pertencem a nenhum grupo sincronizado
- **FR-005**: O sistema MUST expor uma interface para configurar sincronização em `POST /api/2/sync-devices/{username}.json` com corpo JSON contendo, opcionalmente:
  - `synchronize`: lista de grupos-alvo (cada item com 2+ dispositivos) que devem terminar no mesmo grupo
  - `stop-synchronize`: lista de dispositivos que devem sair de qualquer grupo sincronizado
- **FR-006**: Ao processar `synchronize`, o sistema MUST garantir que todos os dispositivos listados em um mesmo item terminem no mesmo grupo sincronizado (unindo grupos existentes quando necessário).
- **FR-007**: Ao processar `stop-synchronize`, o sistema MUST remover cada dispositivo listado de qualquer grupo sincronizado; o dispositivo resultante deve aparecer em `not-synchronized`.
- **FR-008**: O sistema MUST validar que todos os dispositivos referenciados pertencem ao `username` solicitado; caso contrário, MUST rejeitar a solicitação sem aplicar alterações parciais.
- **FR-009**: O sistema MUST responder ao `POST` com o status atualizado no mesmo formato do `GET`.
- **FR-010**: O sistema MUST ser compatível com a versão do contrato indicada como “since 2.10” (ou seja, manter esta interface e formato como estável para clientes que dependem dela).

### Non-Functional Requirements *(mandatory)*

- **NFR-001**: Evidências de verificação MUST incluir testes automatizados para:
  - autorização (acesso ao próprio usuário vs. acesso negado)
  - validação de entrada (dispositivos inexistentes / de outro usuário / duplicatas)
  - idempotência (operações repetidas não mudam o estado)
  - cenários de união e separação de grupos
- **NFR-002**: O recurso MUST manter boas práticas de segurança e privacidade:
  - não expor status de sincronização de outros usuários
  - validar e normalizar entradas para evitar injeções/abuso de payload
  - registrar eventos relevantes (acesso negado, tentativa de referência cruzada de usuário) de forma consistente com o sistema existente
- **NFR-003**: O recurso MUST reutilizar os mecanismos existentes de autenticação, autorização e persistência do sistema; não deve introduzir dependências externas novas sem justificativa explícita no plano.

### Key Entities *(include if feature involves data)*

- **User**: conta proprietária dos dispositivos (identificada por `username`).
- **Device**: um cliente registrado sob um usuário (identificado por um nome único dentro do usuário).
- **Synchronization Group**: agrupamento de 2+ dispositivos do mesmo usuário que compartilham o mesmo estado sincronizado.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Usuários conseguem consultar o status e identificar corretamente (via aplicativo) quais dispositivos estão sincronizados e quais não estão em pelo menos 95% das tentativas com autenticação válida.
- **SC-002**: Usuários conseguem configurar (iniciar/parar) sincronização e observar o status atualizado sem necessidade de tentativa-e-erro em pelo menos 90% dos casos de uso comuns (sincronizar dois dispositivos; parar sincronização de um dispositivo).
- **SC-003**: Tentativas de acesso ao `username` de outro usuário são bloqueadas em 100% dos casos (verificado por testes automatizados).
- **SC-004**: Incidentes de suporte relacionados a “dispositivos não sincronizando por configuração incorreta” reduzem em 25% após disponibilização do recurso (medido em janela definida pelo time de produto).

## Assumptions

- O sistema já possui uma lista de dispositivos registrados por usuário e consegue associar cada nome de dispositivo a um usuário.
- Nomes de dispositivos são strings estáveis e únicas por usuário (não necessariamente globais).
- “Parar sincronização” remove o dispositivo do grupo atual e não altera o agrupamento entre os demais dispositivos do grupo.
- Se um grupo ficar com menos de 2 dispositivos após remoções, ele deixa de ser considerado “sincronizado” e seus dispositivos passam a `not-synchronized`.
- A ordem dos itens nas listas de resposta não é semanticamente relevante; clientes não devem depender de ordenação específica.

## Constitution Alignment *(mandatory)*

- **Slice Integrity**: P1 entrega valor sozinho (visibilidade do status). P2 também é valioso isoladamente (controle de agrupamento) e pode ser validado apenas por mudança observável no status. P3 garante previsibilidade e segurança, reduzindo risco de regressões e vulnerabilidades.
- **Branch Plan**: Implementação será feita no branch `011-device-sync-api`, criado a partir de `main`.
- **Verification Plan**: Deve passar `uv run pytest` e `uv run ruff check .`, além de validações manuais mínimas: (1) consultar status autenticado, (2) sincronizar dois dispositivos, (3) parar sincronização e confirmar status.
- **Quality Gate Strategy**: Ajustes serão feitos no código e nos testes para resolver achados de lint/typing/segurança; não serão usados atalhos como `# noqa`/`# nosec` para esconder problemas.
- **Review Readiness**: O PR final deve resumir: contrato de entrada/saída, decisões de autorização, regras de formação/união/separação de grupos, e matriz de casos de teste cobrindo cenários e bordas.
- **Security/Simplicity Notes**: Risco principal é vazamento de dados entre usuários por autorização incorreta; o plano deve priorizar checagens de autorização e validação de pertencimento do dispositivo antes de aplicar qualquer mudança.
