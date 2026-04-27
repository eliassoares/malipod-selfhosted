# Contract: Archive File Safety

**Feature**: `specs/029-podcast-archive/spec.md`

Rules:
- `archive_path` armazenado no DB deve ser **relativo** e gerado pelo sistema.
- Ao gravar e apagar arquivos, o caminho final resolvido deve permanecer dentro do `ARCHIVE_DIR`.
- Operações de limpeza nunca devem aceitar caminhos vindos diretamente do usuário.
