# Feature Specification: Centralized Subscriptions Sync

**Feature Branch**: `022-centralized-subscriptions-sync`
**Created**: 2026-04-24
**Status**: Draft
**Input**: User description: "Adicionar modo de sincronização centralizada de inscrições no protocolo gpodder: quando ativo, as leituras de inscrições retornam a união distinta de todos os devices do usuário. POST delta changes agrega mudanças de todos os devices, removendo apenas quando ausente em todos. Persistir flag em users (centralize_sync) e adicionar toggle no perfil."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ativar/desativar sincronização centralizada (Priority: P1)

Como usuário autenticado, eu quero ativar ou desativar a sincronização centralizada no meu perfil, para controlar se as inscrições serão lidas por device ou pela união de todos os meus devices.

**Why this priority**: É o controle que habilita todo o comportamento novo e permite que o usuário volte ao modo padrão sem perder compatibilidade.

**Independent Test**: Pode ser testado marcando/desmarcando o toggle na página de perfil e verificando persistência ao recarregar.

**Acceptance Scenarios**:

1. **Given** que estou autenticado, **When** eu habilito “Sincronização centralizada” no meu perfil, **Then** a preferência é salva e permanece após recarregar.
2. **Given** que estou autenticado, **When** eu desabilito “Sincronização centralizada”, **Then** o comportamento volta ao modo padrão.
3. **Given** que tento alterar o perfil de outro usuário, **When** eu envio a atualização, **Then** eu recebo um erro/404 e nenhuma configuração de terceiros é modificada.

---

### User Story 2 - Ler inscrições unificadas via protocolo (Priority: P2)

Como cliente gpodder, eu quero que o endpoint de inscrições retorne a união distinta das inscrições ativas do usuário quando a opção centralizada estiver ativa, para ter uma lista única (transparente) independentemente do device.

**Why this priority**: Habilita o “modo centralizado” como leitura compatível sem exigir mudanças nos clientes.

**Independent Test**: Pode ser testado criando inscrições em devices diferentes e verificando que o `GET` retorna a lista unificada quando ativo e a lista por-device quando inativo.

**Acceptance Scenarios**:

1. **Given** que `centralize_sync` está desligado, **When** eu faço `GET /api/2/subscriptions/{user}/{device}.json`, **Then** eu recebo apenas as inscrições ativas do device informado.
2. **Given** que `centralize_sync` está ligado, **When** eu faço `GET /api/2/subscriptions/{user}/{device}.json`, **Then** eu recebo a união distinta das inscrições ativas do usuário em todos os devices.
3. **Given** que `centralize_sync` está ligado, **When** eu faço `GET /api/2/subscriptions/{user}/{device}.opml`, **Then** eu recebo a mesma união distinta no formato OPML.

---

### User Story 3 - Delta changes centralizado (Priority: P3)

Como cliente gpodder, eu quero que o endpoint de delta changes agregue mudanças de todos os devices quando o modo centralizado estiver ativo, para sincronizar incrementos sem remover podcasts por engano em devices ainda inscritos.

**Why this priority**: Evita efeitos colaterais de remoção em modo centralizado e melhora a consistência multi-device.

**Independent Test**: Pode ser testado gerando eventos de inscrição/desinscrição em múltiplos devices e verificando `add` e `remove` com a regra “remove apenas se removido de todos”.

**Acceptance Scenarios**:

1. **Given** que `centralize_sync` está desligado, **When** eu faço `POST /api/2/subscriptions/{user}/{device}.json` com `since`, **Then** a resposta contém apenas deltas do device informado.
2. **Given** que `centralize_sync` está ligado, **When** eu faço `POST /api/2/subscriptions/{user}/{device}.json` com `since`, **Then** `add` inclui URLs adicionadas em qualquer device desde `since`.
3. **Given** que `centralize_sync` está ligado, **When** eu faço `POST /api/2/subscriptions/{user}/{device}.json` com `since`, **Then** `remove` inclui uma URL apenas se ela estiver ausente das inscrições ativas em todos os devices no momento da leitura (evita remover se ainda existe em algum device).

---

### Edge Cases

- Usuário sem devices: endpoints mantêm comportamento atual de erro/empty-state (sem vazamento de dados).
- Usuário com devices mas sem inscrições: `GET` retorna lista vazia; `POST` retorna `add/remove` vazios.
- Inscrições duplicadas em múltiplos devices: a lista centralizada retorna URLs distintas (sem duplicatas).
- Desinscrição em apenas um device (modo centralizado): não deve aparecer em `remove` se ainda existir em outro device.
- Mudança de `centralize_sync` enquanto clientes sincronizam: leituras passam a seguir a preferência atual, sem quebrar o contrato.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST persist a per-user boolean preference “centralized sync” with default disabled.
- **FR-002**: When centralized sync is disabled, the subscriptions read endpoint MUST return only active subscriptions scoped to the requested device.
- **FR-003**: When centralized sync is enabled, the subscriptions read endpoint MUST return the distinct union of active subscription URLs across all devices belonging to the user.
- **FR-004**: The centralized read behavior MUST apply consistently to both JSON and OPML variants of the subscriptions read endpoint.
- **FR-005**: The delta changes endpoint MUST keep its current behavior when centralized sync is disabled (device-scoped delta).
- **FR-006**: When centralized sync is enabled, the delta changes endpoint MUST aggregate adds across all devices since the provided timestamp.
- **FR-007**: When centralized sync is enabled, the delta changes endpoint MUST include a URL in `remove` only if it is not currently subscribed on any of the user’s devices at read time.
- **FR-008**: The subscriptions write endpoint (`PUT`) MUST remain device-scoped and MUST NOT change behavior due to centralized sync.
- **FR-009**: The profile UI MUST provide a toggle to enable/disable centralized sync for the current user and MUST persist the choice.
- **FR-010**: All endpoints and UI changes MUST enforce cross-account isolation; a user MUST NOT view or change another user’s centralized sync preference or subscriptions via this feature.

### Non-Functional Requirements *(mandatory)*

- **NFR-001**: Verification MUST include automated tests covering both modes (enabled/disabled) for JSON+OPML reads and for delta changes semantics.
- **NFR-002**: The feature MUST maintain protocol compatibility for clients: endpoints and shapes remain unchanged; only results differ by the user preference.
- **NFR-003**: The feature MUST avoid introducing noticeable latency for typical personal usage (a small number of devices/subscriptions).

### Key Entities *(include if feature involves data)*

- **User Preference**: A per-user setting indicating whether centralized sync is enabled.
- **Device Subscription**: A device-scoped record indicating a feed URL is currently subscribed (active) or not.
- **Subscription Change Event**: A record used for delta changes computation since a timestamp.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: With centralized sync enabled, a user can subscribe on one device and see the same feed appear in the read endpoint output for another device without additional writes.
- **SC-002**: With centralized sync enabled, unsubscribing on one device does not produce a `remove` delta if the feed remains subscribed on at least one other device.
- **SC-003**: With centralized sync disabled, behavior matches the current device-scoped implementation (validated by automated tests).
- **SC-004**: The profile toggle persists reliably and is reflected in subsequent protocol reads.

## Assumptions

- “Active subscription” is defined as a device subscription record that is not marked as unsubscribed.
- For centralized delta changes, removals are derived from change events but filtered against the current union of active subscriptions at read time (so “remove” reflects “absent from all”).
- The device parameter remains required by the protocol path, but when centralized sync is enabled it does not restrict reads (it is used only for routing/auth compatibility).
- Episode actions synchronization is out of scope and remains unchanged.

## Constitution Alignment *(mandatory)*

- **Slice Integrity**:
  - US1 is independently valuable (user can control the preference and keep default behavior).
  - US2 is independently valuable (centralized reads improve multi-device UX even without delta aggregation).
  - US3 adds value without changing US2/US1 (delta aggregation correctness).
- **Branch Plan**: Implement on a feature branch created from `main` (`022-centralized-subscriptions-sync`).
- **Verification Plan**: Add/extend contract and integration tests for subscriptions endpoints in both modes, plus UI test for the profile toggle.
- **Quality Gate Strategy**: Pass Ruff, MyPy, Bandit, pip-audit, and pytest without relying on inline suppressions.
- **Review Readiness**: PR summary must explain the semantics change for reads/deltas, list tests added, and call out any compatibility risks.
- **Security/Simplicity Notes**: Centralized mode must not leak cross-user data; implementation should prefer minimal query changes and reuse existing change-event logic.
