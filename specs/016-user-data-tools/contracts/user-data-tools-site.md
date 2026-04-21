# Contract: User Data Tools (Profile Site)

## UI location

Página: `GET /user/profile/{nickname}`

Deve exibir quatro ações somente para o usuário autenticado que corresponde a `{nickname}`:
- Exportar dados
- Importar dados (upload JSON)
- Deletar dados
- Deletar usuário

## Endpoints (proposed)

All endpoints require active session (cookie). If not authenticated: redirect to `/login`.

- `POST /user/profile/{nickname}/export`
  - Response: `200` com `Content-Disposition: attachment; filename="malipod_data_YYYY-MM-DD.json"`
  - Body: JSON snapshot

- `POST /user/profile/{nickname}/import`
  - Request: multipart/form-data com arquivo JSON
  - Response: redirect de volta para o perfil com mensagem de sucesso/erro

- `POST /user/profile/{nickname}/delete-data`
  - Request: confirmação explícita
  - Response: redirect de volta para o perfil (ou login se sessão invalidada)

- `POST /user/profile/{nickname}/delete-user`
  - Request: confirmação explícita
  - Response: revogar sessão + delete cookie + redirect para `/`

## Error handling

- JSON inválido: `400` (ou redirect com mensagem) sem alterar dados
- Arquivo com dados de outro usuário: ignorar (ou tratar como inválido) sem violar isolamento
