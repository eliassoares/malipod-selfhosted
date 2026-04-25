# Quickstart: Web Audio Player Bar

**Feature**: `specs/028-web-audio-player/spec.md`
**Date**: 2026-04-25

## Local Setup

- Subir o app como de costume (PostgreSQL ou o ambiente padrão do projeto).
- Aplicar migrações do Alembic após implementar a feature.

## Manual Verification

### 1) Barra sempre visível

1. Autentique como um usuário.
2. Abra qualquer página (Home/Perfil/Subscrições/Playlists).
3. Verifique que a barra do player aparece no rodapé mesmo sem episódio carregado.

### 2) Iniciar reprodução a partir do episódio

1. Abra `/episode/{id}`.
2. Clique em “Play”.
3. Verifique: título, podcast, capa, play/pause, tempo atual/duração e barra de progresso.

### 3) Navegar sem interromper

1. Com o áudio tocando, navegue para outra página do site.
2. Verifique que o player continua com o mesmo episódio e progresso aproximado.

### 4) Iniciar fila por playlist

1. Abra `/user/{nick}/playlists/{playlist_id}`.
2. Clique “Play Playlist”.
3. Verifique que a fila é definida e o player toca o primeiro episódio.
4. Ao terminar, verificar avanço automático.

### 5) Retomar último episódio

1. Ouça parte de um episódio.
2. Recarregue a página (F5) ou navegue para outra página.
3. Verifique que o player volta em modo pausado com o último episódio e posição.
