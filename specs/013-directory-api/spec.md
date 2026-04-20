# Feature Specification: Directory API

**Feature Branch**: `013-directory-api`
**Created**: 2026-04-19
**Status**: Draft
**Input**: User description: "Directory API pública (sem autenticação) para catálogo local derivado das assinaturas: search/toplist/tags/data (podcast/episode) em JSON/OPML/TXT, com validação 1–100, read-only, `subscribers` por feed e `mygpo_link` usando a URL base configurada no servidor."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Buscar podcasts por nome ou URL (Priority: P1)

Como usuário de um cliente compatível com gpodder.net, eu quero buscar podcasts pelo nome para descobrir e adicionar um podcast ao meu aplicativo sem sair dele.

**Why this priority**: A busca é o fluxo de descoberta mais direto e utilizado. Sem ela, o cliente precisa de uma fonte de busca alternativa.

**Independent Test**: Pode ser testado populando o catálogo local com podcasts assinados e verificando que `GET /search.json?q=termo` retorna apenas podcasts cujo título ou URL do feed contém o termo (case-insensitive).

**Acceptance Scenarios**:

1. **Given** ao menos um usuário com uma assinatura de podcast cujo título contém "linux", **When** um cliente consulta `GET /search.json?q=linux` sem autenticação, **Then** a resposta é `200 OK` com array JSON contendo esse podcast.
2. **Given** uma query sem resultados correspondentes, **When** o cliente busca por um termo inexistente, **Then** a resposta é `200 OK` com array vazio `[]`.
3. **Given** a query com formato `opml`, **When** o cliente consulta `GET /search.opml?q=linux`, **Then** a resposta é OPML válido com os resultados.
4. **Given** a query com formato `txt`, **When** o cliente consulta `GET /search.txt?q=linux`, **Then** a resposta contém uma URL de feed por linha.

---

### User Story 2 - Consultar toplist de podcasts (Priority: P2)

Como usuário de um cliente compatível, eu quero ver quais podcasts são mais populares (mais assinantes) no servidor para descobrir conteúdo relevante.

**Why this priority**: Complementa a busca com descoberta passiva. Valoriza servidores com múltiplos usuários.

**Independent Test**: Pode ser testado com múltiplos usuários assinando o mesmo podcast e verificando que ele aparece na toplist ordenado por número de assinantes.

**Acceptance Scenarios**:

1. **Given** podcasts com diferentes números de assinantes, **When** o cliente consulta `GET /toplist/10.json`, **Then** a resposta lista até 10 podcasts ordenados de forma decrescente por número de assinantes.
2. **Given** `GET /toplist/5.json`, **When** há mais de 5 podcasts no catálogo, **Then** apenas os 5 mais populares são retornados.
3. **Given** uma toplist vazia (nenhum podcast assinado), **When** o cliente consulta `GET /toplist/10.json`, **Then** a resposta é `200 OK` com array vazio.

---

### User Story 3 - Consultar tags e podcasts por tag (Priority: P3)

Como usuário de um cliente compatível, eu quero navegar por categorias/tags para encontrar podcasts de temas específicos.

**Why this priority**: Navegação por tags é um complemento à busca, útil em interfaces que exibem categorias.

**Independent Test**: Pode ser testado com podcasts catalogados com tags (derivadas do feed RSS) e verificando que as rotas de tag retornam os resultados corretos.

**Acceptance Scenarios**:

1. **Given** podcasts no catálogo com tags associadas, **When** o cliente consulta `GET /api/2/tags/10.json`, **Then** a resposta lista até 10 tags mais usadas com campos `title`, `tag` e `usage`.
2. **Given** uma tag `technology` com podcasts associados, **When** o cliente consulta `GET /api/2/tag/technology/5.json`, **Then** a resposta lista até 5 podcasts dessa tag.
3. **Given** uma tag sem podcasts associados, **When** o cliente consulta `GET /api/2/tag/inexistente/10.json`, **Then** a resposta é `200 OK` com array vazio.

---

### User Story 4 - Consultar metadados de podcast ou episódio por URL (Priority: P3)

Como desenvolvedor de cliente, eu quero consultar metadados de um podcast ou episódio a partir da URL do feed para enriquecer a exibição sem re-parsear o RSS.

**Why this priority**: Permite que clientes obtenham dados já normalizados pelo servidor sobre feeds que seus usuários assinam.

**Independent Test**: Pode ser testado consultando a URL de um podcast que existe no catálogo e verificando que os campos esperados estão presentes.

**Acceptance Scenarios**:

1. **Given** um podcast assinado por algum usuário, **When** o cliente consulta `GET /api/2/data/podcast.json?url=<feed_url>`, **Then** a resposta é `200 OK` com objeto contendo `url`, `title`, `author`, `description`, `subscribers`, `logo_url`, `website`, `mygpo_link`.
2. **Given** uma URL de feed não presente no catálogo, **When** o cliente consulta `GET /api/2/data/podcast.json?url=<url>`, **Then** a resposta é `404 Not Found`.
3. **Given** um episódio assinado no catálogo, **When** o cliente consulta `GET /api/2/data/episode.json?podcast=<feed_url>&url=<media_url>`, **Then** a resposta é `200 OK` com objeto contendo `title`, `url`, `podcast_title`, `podcast_url`, `description`, `website`, `released`, `mygpo_link`.
4. **Given** um episódio não presente no catálogo, **When** o cliente consulta `GET /api/2/data/episode.json`, **Then** a resposta é `404 Not Found`.

---

### Edge Cases

- Todos os endpoints são públicos; qualquer requisição sem auth deve ser respondida normalmente.
- O parâmetro `count`/`number` deve ser limitado ao intervalo 1–100; valores fora desse intervalo devem ser rejeitados com `400 Bad Request`.
- Tags devem ser derivadas dos metadados dos feeds RSS já presentes no catálogo local (não há fonte externa).
- O catálogo é composto apenas por podcasts que ao menos um usuário registrado assina; podcasts sem assinantes não aparecem.
- O campo `subscribers` reflete o número de usuários distintos que assinam aquele feed no servidor.
- O campo `mygpo_link` deve usar o `base_url` configurado no servidor (não hardcoded para gpodder.net).
- Formato `opml` e `txt` devem ser suportados nas rotas `/toplist` e `/search` além de `json`.
- O catálogo local é derivado exclusivamente dos podcasts que usuários cadastrados já assinam; nenhuma fonte externa é consultada.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST expor `GET /api/2/tags/{count}.json` retornando as tags mais usadas no catálogo local, sem autenticação.
- **FR-002**: O sistema MUST expor `GET /api/2/tag/{tag}/{count}.json` retornando podcasts com a tag especificada, sem autenticação.
- **FR-003**: O sistema MUST expor `GET /api/2/data/podcast.json?url={feed_url}` retornando metadados do podcast ou `404`.
- **FR-004**: O sistema MUST expor `GET /api/2/data/episode.json?podcast={feed_url}&url={media_url}` retornando metadados do episódio ou `404`.
- **FR-005**: O sistema MUST expor `GET /toplist/{number}.{format}` com `format` em `json`, `opml`, `txt`, retornando podcasts ordenados por número de assinantes decrescente.
- **FR-006**: O sistema MUST expor `GET /search.{format}?q={query}` com `format` em `json`, `opml`, `txt`, retornando podcasts cujo título ou URL do feed corresponde à query (busca case-insensitive por substring).
- **FR-007**: O catálogo MUST incluir apenas podcasts com ao menos uma assinatura ativa no servidor.
- **FR-008**: O campo `subscribers` em todas as respostas MUST refletir o número de usuários distintos que assinam o feed no servidor.
- **FR-009**: O campo `mygpo_link` MUST ser construído com o `base_url` configurado no servidor.
- **FR-010**: Os parâmetros `count` e `number` MUST ser validados no intervalo 1–100; valores inválidos MUST retornar `400 Bad Request`.
- **FR-011**: Tags MUST ser derivadas dos metadados dos feeds RSS já armazenados (campo de categoria/tag do feed); feeds sem categoria não contribuem com tags.

### Non-Functional Requirements *(mandatory)*

- **NFR-001**: Evidências de verificação MUST incluir testes automatizados para:
  - busca por termo com resultados e sem resultados
  - toplist ordenada e limitada por `number`
  - metadados de podcast existente e inexistente
  - metadados de episódio existente e inexistente
  - resposta sem autenticação para todos os endpoints
  - validação do parâmetro `count`/`number` fora do intervalo
- **NFR-002**: O recurso MUST ser read-only; nenhum endpoint escreve dados no banco.
- **NFR-003**: O recurso MUST reutilizar os modelos e dados de assinatura já presentes; não deve duplicar armazenamento de metadados de podcasts.

### Key Entities *(include if feature involves data)*

- **Podcast**: URL do feed, título, autor, descrição, logo, website e categorias/tags já conhecidas pelo servidor a partir de podcasts assinados.
- **Episode**: URL de mídia, título, descrição e data de lançamento já conhecida pelo servidor para episódios do catálogo local.
- **Tag**: derivada das categorias/tags do feed RSS armazenadas; feeds sem categoria não contribuem com tags.
- **Subscribers**: contagem agregada de usuários distintos que assinam um feed (nunca expor lista de usuários).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `GET /search.json?q=<termo>` retorna os podcasts corretos em 100% dos casos de teste com dados populados.
- **SC-002**: `GET /toplist/10.json` retorna podcasts ordenados corretamente por assinantes em 100% dos casos.
- **SC-003**: `GET /api/2/data/podcast.json?url=<url>` retorna `200` para podcasts no catálogo e `404` para URLs desconhecidas em 100% dos casos.
- **SC-004**: Todos os endpoints respondem sem autenticação em 100% das chamadas.

## Assumptions

- Os metadados de podcast (título, autor, logo, categorias) já são armazenados ou deriváveis a partir dos dados existentes de assinatura no servidor.
- Não há indexação de texto completo disponível; a busca por substring simples (LIKE/icontains) é suficiente para o escopo self-hosted.
- Tags são derivadas das categorias do feed RSS; se o feed não tiver categorias, o podcast simplesmente não aparece em navegação por tags.
- O campo `position_last_week` da toplist pode ser omitido ou retornado como `null` pois o histórico de posição não é rastreado nesta versão.
- Formatos `opml` e `txt` nas rotas de toplist e search são compatíveis com os já implementados na Podcast Lists API.
- O catálogo é composto apenas por podcasts com pelo menos uma assinatura ativa; feeds sem assinantes não aparecem.

## Constitution Alignment *(mandatory)*

- **Slice Integrity**: P1 (search) entrega valor independente. P2 (toplist) também é independente. P3 (tags + data endpoints) pode ser entregue após P1 e P2 sem bloquear clientes.
- **Branch Plan**: Implementação no branch `013-directory-api`, criado a partir de `main`.
- **Verification Plan**: Evidências incluem testes automatizados de contrato e integração para os endpoints públicos, além dos checks de qualidade do repositório (lint, tipagem estática e security scan). Validação manual: busca retorna apenas podcasts assinados; toplist ordena corretamente; endpoints de dados retornam `404` para URLs desconhecidas.
- **Quality Gate Strategy**: Sem `# noqa`/`# nosec`. Nenhuma dependência externa nova; dados servidos a partir do catálogo local.
- **Review Readiness**: PR deve documentar como o catálogo é populado, a lógica de contagem de assinantes e o formato de saída de cada endpoint.
- **Security/Simplicity Notes**: Endpoints públicos e read-only. Risco principal é exposição inadvertida de dados de usuários via subscriber count ou mygpo_link; garantir que apenas dados agregados (contagem) sejam expostos, nunca lista de usuários.
