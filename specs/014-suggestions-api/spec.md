# Feature Specification: Suggestions API

**Feature Branch**: `014-suggestions-api`
**Created**: 2026-04-19
**Status**: Draft
**Input**: User description: "Sugestões personalizadas (autenticadas) de podcasts que o usuário ainda não assina, ranqueadas por popularidade global (assinantes distintos), em JSON/OPML/TXT, com validação 1–100, read-only e `mygpo_link` usando a URL base configurada no servidor."

## Contexto

A Suggestions API retorna uma lista personalizada de podcasts que o usuário ainda
não assina, ranqueada por popularidade global no servidor (mais assinantes
distintos = maior prioridade). O endpoint requer autenticação e está disponível
desde v1.0. Formatos suportados: `json`, `opml`, `txt`.

A lógica é intencionalmente simples: usa apenas a popularidade agregada do
catálogo local e exclui da resposta tudo o que o usuário já assina. Nunca expõe
lista de usuários — apenas contagens agregadas.

**Dependência**: esta feature depende da Directory API (spec 013) porque o catálogo de podcasts precisa existir antes de sugestões fazerem sentido.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Receber sugestões de podcasts não assinados (Priority: P1)

Como usuário autenticado, eu quero receber uma lista de podcasts populares no
servidor que eu ainda não assino para descobrir novos conteúdos sem precisar
buscar manualmente.

**Why this priority**: É o valor central do endpoint. Sem ele, a Suggestions API não existe.

**Independent Test**: Pode ser testado com dois usuários onde um assina um podcast que o outro não assina. O usuário sem a assinatura deve ver o podcast do outro como sugestão.

**Acceptance Scenarios**:

1. **Given** usuário A assina `podcast-x` e usuário B não assina `podcast-x`, **When** usuário B consulta `GET /suggestions/5.json`, **Then** `podcast-x` aparece na resposta.
2. **Given** usuário B já assina `podcast-y`, **When** usuário B consulta `GET /suggestions/10.json`, **Then** `podcast-y` NÃO aparece na resposta.
3. **Given** um usuário sem nenhuma assinatura, **When** consulta `GET /suggestions/10.json`, **Then** a resposta é `200 OK` com array vazio `[]` (sem podcasts para cruzar).
4. **Given** `GET /suggestions/5.json`, **When** há 20 podcasts elegíveis, **Then** a resposta contém no máximo 5 itens.

---

### User Story 2 - Receber sugestões em múltiplos formatos (Priority: P2)

Como desenvolvedor de cliente, eu quero receber as sugestões em formato OPML ou TXT além de JSON para importar diretamente em leitores que aceitam esses formatos.

**Why this priority**: Consistência com os outros endpoints de listagem (toplist, search, podcast lists).

**Independent Test**: Pode ser testado consultando `/suggestions/5.opml` e `/suggestions/5.txt` e verificando que os formatos são válidos.

**Acceptance Scenarios**:

1. **Given** sugestões disponíveis para o usuário, **When** o cliente consulta `GET /suggestions/5.opml`, **Then** a resposta é OPML válido com os podcasts sugeridos.
2. **Given** sugestões disponíveis para o usuário, **When** o cliente consulta `GET /suggestions/5.txt`, **Then** a resposta contém uma URL de feed por linha.

---

### User Story 3 - Acesso negado sem autenticação (Priority: P3)

Como operador do servidor, eu quero garantir que sugestões personalizadas só sejam acessíveis por usuários autenticados para proteger dados de assinatura.

**Why this priority**: Sugestões revelam padrões de assinatura do servidor; devem ser protegidas.

**Independent Test**: Pode ser testado consultando o endpoint sem credenciais e verificando resposta 401.

**Acceptance Scenarios**:

1. **Given** uma requisição sem autenticação, **When** o cliente consulta `GET /suggestions/5.json`, **Then** a resposta é `401 Unauthorized`.

---

### Edge Cases

- O parâmetro `number` deve ser limitado ao intervalo 1–100; valores fora desse intervalo retornam `400 Bad Request`.
- Podcasts que o usuário já assina nunca devem aparecer nas sugestões, mesmo que sejam os mais populares do servidor.
- Se o servidor tem apenas um usuário, não há outros perfis para comparar; a resposta deve ser `200 OK` com array vazio.
- O campo `mygpo_link` nas sugestões MUST usar o `base_url` configurado no servidor.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST expor `GET /suggestions/{number}.{format}` com `format` em `json`, `opml`, `txt`.
- **FR-002**: O endpoint MUST exigir autenticação (Basic Auth ou session cookie).
- **FR-003**: A resposta MUST conter no máximo `number` podcasts que o usuário autenticado NÃO assina atualmente.
- **FR-004**: O sistema MUST excluir da resposta todos os podcasts que o usuário autenticado já assina.
- **FR-005**: A lógica de ranking MUST priorizar podcasts mais populares globalmente no servidor (maior número de assinantes distintos) entre os não assinados pelo usuário.
- **FR-006**: O sistema MUST retornar `200 OK` com array vazio quando não houver sugestões disponíveis (ex.: servidor com um único usuário, ou usuário já assina tudo).
- **FR-007**: O parâmetro `number` MUST ser validado no intervalo 1–100; valores inválidos MUST retornar `400 Bad Request`.
- **FR-008**: O campo `mygpo_link` MUST ser construído com o `base_url` configurado no servidor.
- **FR-009**: Cada item da resposta JSON MUST conter os campos: `url`, `title`, `author`, `description`, `subscribers`, `logo_url`, `website`, `mygpo_link`.

### Non-Functional Requirements *(mandatory)*

- **NFR-001**: Evidências de verificação MUST incluir testes automatizados para:
  - autenticação obrigatória (401 sem credenciais)
  - exclusão de podcasts já assinados pelo usuário
  - limite de `number` respeitado
  - resposta vazia quando não há sugestões
  - validação do parâmetro `number` fora do intervalo
- **NFR-002**: O recurso MUST ser read-only; não escreve dados no banco.
- **NFR-003**: O recurso MUST reutilizar os mecanismos de autenticação existentes (`authenticate_api_user`) e os dados de assinatura já persistidos; não deve introduzir dependências externas.
- **NFR-004**: A query de sugestões MUST ser eficiente o suficiente para retornar em tempo razoável (< 500ms) para servidores self-hosted com até 100 usuários e 500 podcasts distintos.

### Key Entities *(include if feature involves data)*

- **User**: usuário autenticado cujas assinaturas são excluídas das sugestões.
- **Podcast** (catálogo local): fonte dos candidatos a sugestão.
- **Subscription**: usada para determinar quais podcasts o usuário já assina e para calcular popularidade (subscribers count por podcast).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `GET /suggestions/10.json` retorna apenas podcasts não assinados pelo usuário autenticado em 100% dos casos de teste.
- **SC-002**: O endpoint retorna `401` em 100% das requisições sem autenticação.
- **SC-003**: O limite `number` é respeitado em 100% dos casos (resposta nunca contém mais itens que o solicitado).
- **SC-004**: Resposta vazia (`[]`) é retornada corretamente quando não há sugestões disponíveis.

## Assumptions

- O catálogo de podcasts deriva das assinaturas existentes (conforme spec 013 — Directory API); esta feature depende desse catálogo estar acessível.
- A estratégia de recomendação é popularidade global simples (mais assinantes = maior prioridade); filtro colaborativo complexo está fora do escopo.
- Podcasts com `logo_url` nulo são válidos; o campo pode ser `null` na resposta.
- O parâmetro `jsonp` documentado na spec original (disponível desde v2.8) está fora do escopo desta implementação; não há suporte a JSONP.
- Assinaturas deletadas (ou devices removidos) não contam como assinatura ativa para efeito de exclusão ou contagem.

## Constitution Alignment *(mandatory)*

- **Slice Integrity**: P1 (sugestões em JSON) entrega o valor principal completo e independente. P2 (formatos OPML/TXT) é incremental. P3 (segurança) é pré-requisito implícito de P1.
- **Branch Plan**: Implementação no branch `014-suggestions-api`, criado a partir de `main` (após merge de `013-directory-api`).
- **Verification Plan**: Deve passar `uv run pytest` e `uv run ruff check .`. Validação manual: autenticar com usuário que tem assinaturas e verificar que sugestões não incluem podcasts já assinados.
- **Quality Gate Strategy**: Sem `# noqa`/`# nosec`. Consultas devem ser eficientes e evitar trabalho redundante; reutilizar padrões de service existentes.
- **Review Readiness**: PR deve documentar a query de ranking usada, os critérios de exclusão e os casos de borda com servidor de usuário único.
- **Security/Simplicity Notes**: O endpoint expõe dados derivados do comportamento de outros usuários (popularidade); nunca expor lista de usuários ou atribuir sugestão a um usuário específico. Risco é baixo pois apenas contagens agregadas são expostas.
