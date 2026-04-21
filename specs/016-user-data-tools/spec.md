# Feature Specification: User Data Tools

**Feature Branch**: `016-user-data-tools`
**Created**: 2026-04-20
**Status**: Draft
**Input**: User description: "Adicionar 4 novo botões na página de usuário: deletar dados (varrer tabelas com user_id exceto users + dados relacionados a devices via device_pk), deletar usuário (inclui users; deslogar e redirecionar para home), exportar dados (JSON por tabela, sem password_hash/password_salt), importar dados (upsert por chaves/recência conforme screenshots)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Exportar meus dados (Priority: P1)

Como usuário logado, eu quero exportar meus dados do Malipod para poder fazer
backup e migrar/recuperar minha conta e configurações.

**Why this priority**: Backup é a forma mais segura de preservar dados do usuário
antes de limpeza, troca de servidor, ou reimportação.

**Independent Test**: Pode ser testado logando, clicando em “Exportar dados” e
verificando que um arquivo JSON é baixado, contendo campos por tabela e sem
informações sensíveis de senha.

**Acceptance Scenarios**:

1. **Given** um usuário logado, **When** solicita exportação, **Then** recebe um
   arquivo JSON com um campo por tabela relevante (ex.: `"users"`, `"devices"`, etc.).
2. **Given** um usuário logado, **When** exporta, **Then** o campo `"users"` não
   inclui `password_hash` nem `password_salt`.
3. **Given** um usuário logado, **When** exporta, **Then** a exportação NÃO inclui
   sessões autenticadas (dados efêmeros).
4. **Given** um usuário logado, **When** exporta, **Then** o nome do arquivo segue
   o padrão `malipod_data_{DATA_ATUAL}.json`.

---

### User Story 2 - Importar meus dados com segurança (Priority: P2)

Como usuário logado, eu quero importar um arquivo JSON previamente exportado
para restaurar meus dados, sem sobrescrever dados mais novos que já existem no servidor.

**Why this priority**: Restauração deve ser segura; importações não podem causar
perda de dados recentes por engano.

**Independent Test**: Pode ser testado importando um JSON válido e verificando
que os registros são aplicados nas tabelas correspondentes; e que registros
antigos não substituem registros mais recentes no banco.

**Acceptance Scenarios**:

1. **Given** um usuário logado e um arquivo exportado válido, **When** importa,
   **Then** os dados são carregados nas tabelas correspondentes.
2. **Given** um registro no arquivo mais antigo que o registro existente no banco
   (comparação pela “coluna de recência” definida por tabela), **When** importa,
   **Then** esse registro é ignorado (não atualiza o banco).
3. **Given** um registro no arquivo mais recente que o do banco, **When** importa,
   **Then** esse registro atualiza o existente.
4. **Given** tabelas de eventos append-only, **When** importa, **Then** apenas
   insere quando o evento ainda não existe e nunca atualiza eventos já presentes.

---

### User Story 3 - Limpar meus dados mantendo a conta (Priority: P3)

Como usuário logado, eu quero deletar meus dados (associações, ações, configurações
e dados relacionados a meus dispositivos) sem remover minha conta de usuário.

**Why this priority**: Permite “reset” do estado do usuário sem precisar recriar
conta e credenciais.

**Independent Test**: Pode ser testado criando dados de usuário/dispositivos,
executando “Deletar dados” e verificando que não há mais registros associados ao
usuário/dispositivos, mas o registro em `users` ainda existe.

**Acceptance Scenarios**:

1. **Given** um usuário logado com dados em tabelas associadas, **When** executa
   “Deletar dados”, **Then** todos os registros ligados ao usuário são removidos,
   exceto o registro em `users`.
2. **Given** um usuário logado com devices, **When** executa “Deletar dados”,
   **Then** registros ligados aos devices do usuário também são removidos (inclusive
   os que referenciam por `device_pk`).

---

### User Story 4 - Deletar minha conta e sair (Priority: P4)

Como usuário logado, eu quero deletar meu usuário e todos os seus dados para
remover completamente minha presença do servidor e ser deslogado em seguida.

**Why this priority**: Oferece controle total sobre dados pessoais e remoção da conta.

**Independent Test**: Pode ser testado criando um usuário, logando, acionando
“Deletar usuário” e verificando redirecionamento para `/` sem sessão ativa.

**Acceptance Scenarios**:

1. **Given** um usuário logado, **When** executa “Deletar usuário”, **Then** todos
   os dados ligados ao usuário são removidos incluindo o registro em `users`.
2. **Given** a remoção completa, **When** a operação termina, **Then** o usuário é
   deslogado e redirecionado para a página inicial (`/`).

---

### Edge Cases

- Importação deve rejeitar arquivos inválidos ou fora do formato esperado com mensagem clara.
- Operações destrutivas (deletar dados / deletar usuário) devem exigir confirmação explícita do usuário.
- Importação/exportação não devem expor nem aceitar campos de senha.
- O usuário não deve conseguir operar sobre dados de outro usuário, mesmo alterando o arquivo importado.
- Sessões autenticadas não devem ser importadas/exportadas.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST adicionar 4 ações na página do usuário logado: **Exportar dados**, **Importar dados**, **Deletar dados**, **Deletar usuário**.
- **FR-002**: As ações MUST estar disponíveis apenas para o usuário autenticado (não para visitantes).
- **FR-003**: Exportação MUST gerar um arquivo JSON com um campo por tabela exportada (ex.: `"users"`, `"devices"`, ...).
- **FR-004**: Exportação MUST incluir a tabela `users` mas MUST remover `password_hash` e `password_salt` do conteúdo exportado.
- **FR-005**: Exportação MUST ignorar tabelas de sessão/autenticação efêmeras (ex.: sessões autenticadas).
- **FR-006**: Importação MUST aceitar apenas JSON no formato exportado e MUST carregar cada campo do JSON na tabela correspondente.
- **FR-007**: Importação MUST aplicar regras de merge por tabela: usar “chave natural” para localizar registro e “coluna de recência” para decidir atualizar/ignorar.
- **FR-008**: Para tabelas marcadas como append-only, importação MUST apenas inserir quando o registro não existe e MUST NOT atualizar registros existentes.
- **FR-009**: “Deletar dados” MUST remover todos os registros associados ao usuário (tabelas com `user_id`), exceto `users`.
- **FR-010**: “Deletar dados” MUST remover também dados associados a devices do usuário incluindo tabelas que referenciam devices por `device_pk`.
- **FR-011**: “Deletar usuário” MUST executar a limpeza completa (equivalente a “Deletar dados”) e MUST também remover o registro do usuário em `users`.
- **FR-012**: Após “Deletar usuário”, o sistema MUST encerrar a sessão do usuário e redirecionar para `/`.
- **FR-013**: O nome do arquivo de exportação MUST seguir o padrão `malipod_data_{DATA_ATUAL}.json`.
- **FR-014**: As regras de chaves naturais e recência por tabela MUST seguir o mapeamento definido nas screenshots fornecidas.

### Non-Functional Requirements *(mandatory)*

- **NFR-001**: Evidências de verificação MUST incluir testes automatizados para:
  - visibilidade dos 4 botões apenas quando logado
  - exportação gera JSON e não inclui `password_hash`/`password_salt`
  - importação ignora registros mais antigos e atualiza registros mais recentes
  - deleção de dados não remove `users`
  - deleção de usuário remove `users` e encerra sessão + redirect para `/`
  - `uv run pytest` e `uv run ruff check .` passando
- **NFR-002**: Operações destrutivas MUST ser seguras (confirmação explícita, e execução atômica por transação quando possível).
- **NFR-003**: Importação MUST ser segura contra escalonamento (não permitir importar/alterar dados de outros usuários).
- **NFR-004**: Export/import MUST ser eficiente o suficiente para uso self-hosted (operações concluindo em tempo razoável para contas típicas).

### Key Entities *(include if feature involves data)*

- **User**: usuário autenticado que exporta/importa e aciona ações destrutivas.
- **Device**: dispositivos do usuário; dados associados devem ser considerados em export/import e limpeza.
- **User Data Snapshot**: arquivo JSON exportado contendo dados por tabela.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Exportação gera JSON válido e sem `password_hash`/`password_salt` em 100% dos testes.
- **SC-002**: Importação nunca sobrescreve dados mais recentes com dados mais antigos em 100% dos testes.
- **SC-003**: “Deletar dados” remove todos os dados associados (exceto `users`) em 100% dos testes.
- **SC-004**: “Deletar usuário” remove o usuário e desloga/redireciona em 100% dos testes.

## Assumptions

- O usuário precisa estar autenticado para acessar a página de perfil e acionar as ações.
- Sessões autenticadas são efêmeras e não fazem parte de backup/restauração.
- “Coluna de recência” por tabela corresponde aos timestamps indicados nas screenshots (ex.: `updated_at`, `occurred_at`, `created_at`).
- A importação opera apenas no escopo do usuário logado (mesmo que o arquivo contenha dados de outros usuários, eles são ignorados).

## Constitution Alignment *(mandatory)*

- **Slice Integrity**: P1 (export) entrega valor isolado e seguro; P2 adiciona restore com merge seguro; P3/P4 são operações destrutivas separadas e testáveis.
- **Branch Plan**: Implementação no branch `016-user-data-tools`, criado a partir de `main`.
- **Verification Plan**: Rodar `uv run pytest` e `uv run ruff check .` e validar fluxos de export/import/delete com testes de contrato/integration.
- **Quality Gate Strategy**: Sem `# noqa`/`# nosec`; corrigir issues na raiz.
- **Review Readiness**: PR deve sumarizar tabelas cobertas, regras de merge/recência e salvaguardas de segurança.
- **Security/Simplicity Notes**: Exportação não inclui segredos; importação restringe ao usuário atual; deleções exigem confirmação explícita.
