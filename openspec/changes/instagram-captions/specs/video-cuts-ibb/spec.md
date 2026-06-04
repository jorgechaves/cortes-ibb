## MODIFIED Requirements

### Requirement: Upload para Google Drive
O sistema SHALL fazer upload, para a pasta `videos-ibb/[YYYY-MM-DD]` no Google Drive, dos 6 arquivos MP4 finais **mais** os arquivos de legenda de Instagram quando disponíveis: `instagram.md` (mimeType `text/markdown`) e `corte-01-instagram.txt` a `corte-06-instagram.txt` (mimeType `text/plain`). Quando as legendas foram puladas (`instagram_skipped=true`), o sistema SHALL fazer upload apenas dos MP4. O acesso SHALL continuar usando OAuth do Google com token em `~/.config/cortes-ibb/`.

#### Scenario: Upload completo (com legendas)
- **WHEN** o pipeline gera os 6 MP4 + legendas Instagram
- **THEN** a subpasta no Drive recebe 13 arquivos (6 MP4 + 1 `.md` + 6 `.txt`), todos com nome preservado e mimeType correto

#### Scenario: Upload sem legendas (estágio pulado)
- **WHEN** o pipeline pulou o estágio `instagram` (sem key OU falha de API)
- **THEN** a subpasta no Drive recebe apenas os 6 MP4

#### Scenario: Falha em upload
- **WHEN** o upload de um ou mais arquivos falha
- **THEN** o pipeline emite evento `error` listando os arquivos afetados, mantém todos os artefatos locais e oferece retry via UI ou via `reupload.py`
