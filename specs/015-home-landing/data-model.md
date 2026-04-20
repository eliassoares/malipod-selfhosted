# Data Model: Home Landing Page

**Feature**: `015-home-landing` | **Date**: 2026-04-20

## Scope

Sem mudanças de modelo persistido.

## Existing Entities

### Session / Current User

- Fonte: cookie de sessão + `AuthService.get_active_session(...)`
- Uso: determinar quais CTAs aparecem na home (`current_user` presente ou ausente).
