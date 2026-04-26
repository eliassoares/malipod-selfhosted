# Feature Specification: Web Audio Player Bar

**Feature Branch**: `028-web-audio-player`
**Created**: 2026-04-25
**Status**: Draft
**Input**: User description: "Barra de áudio persistente no rodapé, com fila (playlist/podcast), retomada do último episódio e sincronização do histórico de reprodução via um device web dedicado."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reproduzir com barra persistente (Priority: P1)

Como usuário autenticado, quero iniciar a reprodução de um episódio e controlar o áudio por uma barra fixa no rodapé, para continuar ouvindo enquanto navego entre páginas do site sem perder o progresso.

**Why this priority**: Entrega valor imediato: ouvir episódios com uma experiência consistente no site inteiro, sem interrupções ao navegar.

**Independent Test**: Pode ser testado iniciando a reprodução de um episódio e navegando para outra página; a barra continua visível e mantém o estado (episódio, tempo atual e play/pause).

**Acceptance Scenarios**:

1. **Given** um usuário autenticado e nenhum episódio ativo, **When** a página é carregada, **Then** a barra do player aparece no rodapé em estado inativo/vazio.
2. **Given** um usuário autenticado em uma página de episódio, **When** ele inicia a reprodução, **Then** a barra do player exibe capa, título do episódio, nome do podcast, controles e progresso atual.
3. **Given** uma reprodução em andamento, **When** o usuário navega para outra página do site, **Then** o player mantém o episódio carregado e o progresso é restaurado na nova página (sem reiniciar do zero).

---

### User Story 2 - Fila e avanço automático (Priority: P2)

Como usuário, quero iniciar uma fila de reprodução a partir de uma playlist ou do próprio podcast para ouvir episódios em sequência, avançando automaticamente ao final de cada episódio.

**Why this priority**: Depois de “play contínuo” existir, a fila reduz fricção e aumenta tempo de uso (binge listening) com previsibilidade.

**Independent Test**: Pode ser testado iniciando a reprodução a partir de uma playlist e verificando que o player avança para o próximo episódio quando o atual termina.

**Acceptance Scenarios**:

1. **Given** uma playlist com vários episódios, **When** o usuário inicia a reprodução pela playlist, **Then** o player toca os episódios na ordem definida e avança automaticamente ao terminar cada um.
2. **Given** um episódio de um podcast, **When** o usuário inicia a reprodução nesse episódio (modo podcast), **Then** ao terminar o episódio atual o player avança para o próximo episódio do mesmo podcast conforme a ordem por data.

---

### User Story 3 - Retomar e registrar histórico (Priority: P3)

Como usuário, quero retomar automaticamente meu último episódio e progresso quando volto ao site, e quero que o histórico de reprodução reflita play/pause/conclusão para que métricas e histórico do app permaneçam consistentes.

**Why this priority**: Evita “perder onde estava” e mantém métricas/histórico coerentes com o restante do sistema.

**Independent Test**: Pode ser testado reproduzindo parte de um episódio, saindo do site e voltando; o player aparece pausado com o mesmo episódio e progresso aproximado, e o histórico do usuário registra os eventos essenciais.

**Acceptance Scenarios**:

1. **Given** que o usuário ouviu um episódio anteriormente, **When** ele abre qualquer página autenticada, **Then** o player inicia em modo pausado com o último episódio e o último progresso salvo.
2. **Given** uma reprodução com interações (play/pause/final do episódio), **When** o usuário executa essas ações, **Then** o sistema registra no histórico do usuário eventos que permitam calcular plays e conclusão do episódio.

---

### Edge Cases

- O que acontece quando o episódio não possui mídia reproduzível ou a reprodução falha? (o player deve mostrar erro amigável e não travar a navegação)
- O que acontece quando a fila acaba (último episódio termina)? (o player deve parar e permanecer com o episódio concluído exibido)
- O que acontece quando o usuário desloga durante a navegação? (o player deve voltar ao estado inativo e não registrar eventos adicionais)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O site MUST exibir uma barra de player fixa no rodapé em todas as páginas (incluindo estado vazio quando não há episódio carregado).
- **FR-002**: Usuários MUST conseguir iniciar reprodução a partir de um episódio e controlar play/pause, avanço e retorno de tempo, e fazer scrub no progresso.
- **FR-003**: O player MUST manter o estado do episódio atual ao navegar entre páginas do site durante a mesma sessão de navegação.
- **FR-004**: O sistema MUST suportar fila de reprodução em dois modos:
  - **Playlist**: fila derivada de uma playlist escolhida pelo usuário.
  - **Podcast**: fila derivada do podcast do episódio atual, ordenada por data.
- **FR-005**: Ao término de um episódio, o player MUST avançar automaticamente para o próximo item da fila (quando existir).
- **FR-006**: O sistema MUST salvar o “último episódio” e “último progresso” do usuário de forma recorrente durante a reprodução e sempre que o usuário pausar/parar, permitindo retomar posteriormente.
- **FR-007**: Ao carregar páginas autenticadas, o site MUST inicializar o player com o último episódio/progresso conhecido em modo pausado (quando existirem dados).
- **FR-008**: O sistema MUST registrar no histórico do usuário eventos suficientes para representar: início de reprodução, pausa e conclusão do episódio.
- **FR-009**: O sistema MUST associar os eventos do player web a uma identidade de reprodução “web player” por usuário, criada de forma idempotente.
- **FR-010**: O sistema MUST validar que ações e estado do player só podem ser registrados por usuários autenticados e apenas para o próprio usuário.

### Non-Functional Requirements *(mandatory)*

- **NFR-001**: Evidências de verificação MUST incluir:
  - testes automatizados cobrindo persistência do último episódio/progresso e idempotência da identidade de reprodução web;
  - testes automatizados cobrindo registro de eventos essenciais no histórico;
  - testes automatizados confirmando que páginas autenticadas incluem a barra do player no HTML;
  - checagens estáticas e de segurança já exigidas pelo projeto.
- **NFR-002**: O recurso MUST tratar entradas inválidas e estados inesperados sem expor dados de outros usuários (owner-only) e sem quebrar a navegação do site.
- **NFR-003**: A experiência MUST ser mobile friendly e manter consistência visual com as páginas existentes.

### Key Entities *(include if feature involves data)*

- **Player State**: Estado persistido por usuário (último episódio, progresso e modo de fila) para retomada ao voltar ao site.
- **Playback Queue**: Lista ordenada de episódios a serem reproduzidos automaticamente (derivada de playlist ou podcast).
- **Web Playback Identity**: Identidade de reprodução do player web associada ao usuário para registro coerente do histórico.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Um usuário consegue iniciar reprodução de um episódio e navegar para outra página sem perder o episódio atual e sem reiniciar o progresso.
- **SC-002**: Ao voltar ao site após ouvir parcialmente um episódio, o usuário vê o player pausado com o mesmo episódio e com o progresso salvo com precisão suficiente para retomar (diferença máxima de 10 segundos em relação ao último salvamento).
- **SC-003**: Em uma playlist com pelo menos 3 episódios, o player avança automaticamente para o próximo episódio ao concluir o atual, até o fim da fila.
- **SC-004**: O histórico do usuário reflete ações de play/pause/conclusão, permitindo calcular “vezes reproduzido” e “concluído” de forma consistente.

## Assumptions

- O usuário está autenticado para iniciar e registrar ações do player.
- Episódios possuem dados suficientes para exibição (título, podcast associado e um link de mídia quando reproduzível).
- A retomada entre páginas cobre navegação tradicional (troca de página), sem exigir experiência de aplicativo single-page.
- Persistência de fila entre sessões completas do navegador (fechar/reabrir) não é exigida nesta fase.

## Constitution Alignment *(mandatory)*

- **Slice Integrity**: US1 entrega valor sozinho (player persistente); US2 adiciona valor incremental (fila/auto-avanço); US3 adiciona valor incremental (retomada + histórico) e é testável de forma independente.
- **Branch Plan**: A implementação ocorrerá no branch `028-web-audio-player`, criado a partir de `main`.
- **Verification Plan**: Antes do merge, devem passar: suíte de testes, lint/format, checagem de tipos e checagens de segurança usadas no repositório.
- **Quality Gate Strategy**: Ajustes serão feitos no código para resolver achados (formatação, lint, tipos e segurança) sem suprimir avisos como atalho.
- **Review Readiness**: O PR final deve resumir: UX do player, regras de fila (playlist/podcast), persistência de estado e como o histórico do usuário é atualizado, com evidências de testes.
- **Security/Simplicity Notes**: A maior superfície de risco é registrar eventos/estado indevidos; a solução deve manter owner-only e validação estrita de entradas, evitando complexidade desnecessária.
