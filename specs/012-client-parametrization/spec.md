# Feature Specification: Client Parametrization

**Feature Branch**: `012-client-parametrization`
**Created**: 2026-04-19
**Status**: Draft
**Input**: User description: "Adicionar `GET /clientconfig.json` público e stateless para auto-configuração de clientes gpodder-compatíveis, retornando `mygpo.baseurl` (normalizado com trailing slash) e `update_timeout`."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Auto-configurar cliente a partir do servidor (Priority: P1)

Como usuário que instala um aplicativo compatível com gpodder.net apontando para um servidor MaliPod, eu quero que o aplicativo descubra automaticamente os endereços base da API sem configuração manual para não precisar digitar URLs internamente.

**Why this priority**: Sem esse endpoint, clientes precisam hardcodar a URL base. Com ele, o cliente pode consultar uma URL canônica e auto-configurar todos os endpoints de API a partir do campo `baseurl`.

**Independent Test**: Pode ser testado consultando `GET /clientconfig.json` sem autenticação e verificando que o JSON retornado contém `mygpo.baseurl` apontando para o endereço configurado no servidor.

**Acceptance Scenarios**:

1. **Given** um servidor MaliPod em execução, **When** um cliente consulta `GET /clientconfig.json` sem autenticação, **Then** a resposta é `200 OK` com JSON contendo `mygpo.baseurl` igual à URL base configurada no servidor.
2. **Given** um servidor com URL base configurada como `https://meu.servidor.com`, **When** o cliente lê `mygpo.baseurl`, **Then** o valor é `https://meu.servidor.com/` (com trailing slash) para que a concatenação de paths funcione corretamente.

---

### User Story 2 - Indicar validade da configuração ao cliente (Priority: P2)

Como operador do servidor, eu quero poder indicar por quanto tempo os clientes devem cachear a configuração para não sobrecarregar o servidor com requisições repetidas.

**Why this priority**: Permite que clientes façam refresh periódico sem polling excessivo.

**Independent Test**: Pode ser testado verificando que o campo `update_timeout` está presente na resposta e contém um valor numérico positivo (em segundos).

**Acceptance Scenarios**:

1. **Given** a resposta de `GET /clientconfig.json`, **When** o cliente lê `update_timeout`, **Then** o valor é um inteiro positivo representando segundos de validade da configuração.

---

### Edge Cases

- A requisição sem `Accept` header deve retornar JSON com `Content-Type: application/json`.
- O endpoint não exige autenticação; qualquer requisição deve ser respondida.
- Se a URL base configurada não tiver trailing slash, o servidor deve normalizá-la ao retornar `baseurl`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST expor `GET /clientconfig.json` sem exigir autenticação.
- **FR-002**: A resposta MUST ser JSON com pelo menos o objeto `mygpo` contendo o campo `baseurl` (string, URL base do servidor).
- **FR-003**: O campo `mygpo.baseurl` MUST corresponder ao valor de URL base configurado no servidor.
- **FR-004**: A resposta MUST incluir o campo `update_timeout` com valor inteiro em segundos indicando por quanto tempo o cliente pode cachear a configuração.
- **FR-005**: O `Content-Type` da resposta MUST ser `application/json`.
- **FR-006**: O sistema SHOULD incluir o objeto `mygpo-feedservice` com `baseurl` para compatibilidade máxima com clientes, mesmo que o feed service não esteja implementado (pode ser o mesmo valor de URL base do servidor).

### Non-Functional Requirements *(mandatory)*

- **NFR-001**: Evidências de verificação MUST incluir testes automatizados para:
  - resposta 200 sem autenticação
  - presença e formato correto dos campos `mygpo.baseurl` e `update_timeout`
  - valor de `baseurl` refletindo a URL base configurada no servidor
- **NFR-002**: O endpoint MUST ser stateless e não realizar nenhuma operação de escrita no banco de dados.
- **NFR-003**: O recurso MUST reutilizar a configuração existente de URL base do servidor; não deve introduzir nova configuração.

### Key Entities *(include if feature involves data)*

- **Settings**: configuração do servidor (URL base) usada para construir a resposta.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Clientes gpodder-compatíveis conseguem auto-configurar a URL base a partir de `GET /clientconfig.json` em 100% das tentativas quando a URL base do servidor está corretamente configurada.
- **SC-002**: O endpoint responde sem autenticação em 100% das chamadas.
- **SC-003**: O campo `mygpo.baseurl` está presente e contém uma URL válida em 100% das respostas.

## Assumptions

- A URL base do servidor já é uma configuração existente (usada em outras partes do sistema).
- Clientes compatíveis com gpodder.net consultam `GET /clientconfig.json` antes de usar qualquer outro endpoint para descobrir a URL base.
- O campo `mygpo-feedservice.baseurl` pode apontar para o mesmo valor de URL base do servidor sem quebrar clientes; feed service não é implementado.
- O valor de `update_timeout` pode ser um valor fixo razoável (ex.: 86400 segundos = 24 horas).

## Constitution Alignment *(mandatory)*

- **Slice Integrity**: P1 (baseurl) entrega o valor principal completo; P2 (update_timeout) é complementar e pode ser entregue junto sem overhead.
- **Branch Plan**: Implementação no branch `012-client-parametrization`, criado a partir de `main`.
- **Verification Plan**: Deve passar a suíte de testes automatizados e os checks de estilo/qualidade do repositório. Validação manual: consultar `GET /clientconfig.json` sem credenciais deve retornar JSON com `mygpo.baseurl`.
- **Quality Gate Strategy**: Sem atalhos `# noqa`/`# nosec`. Nenhuma dependência nova necessária.
- **Review Readiness**: PR deve resumir o contrato de resposta e confirmar que `baseurl` reflete a config do servidor.
- **Security/Simplicity Notes**: Endpoint público, stateless, sem risco de exposição de dados sensíveis. Implementação deve ser trivial (handler direto, sem camada de serviço).
