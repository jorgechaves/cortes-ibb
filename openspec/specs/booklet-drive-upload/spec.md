# Spec: booklet-drive-upload

## Purpose

Faz upload do livreto PDF gerado para o Google Drive, armazenando-o na subpasta `livros/` dentro da pasta-raiz do projeto, criando a subpasta automaticamente se necessário.

## Requirements

### Requirement: Upload do livreto ao Google Drive na subpasta livros
O sistema SHALL fazer upload do arquivo `livreto.pdf` gerado para o Google Drive na subpasta `livros/` dentro da pasta-raiz do projeto (`TARGET_FOLDER_ID` em `pipeline/drive.py`). A subpasta `livros/` SHALL ser criada automaticamente se não existir.

#### Scenario: Upload bem-sucedido para subpasta livros
- **WHEN** o livreto PDF é gerado com sucesso e as credenciais Drive estão disponíveis
- **THEN** o arquivo `livreto.pdf` é enviado para `Drive/livros/livreto.pdf`, o sistema emite `type: log, message: "Livreto enviado para Drive/livros/"`, e o resultado SSE `type: done` inclui `booklet_drive_url`

#### Scenario: Subpasta livros criada automaticamente
- **WHEN** a subpasta `livros/` não existe na pasta-raiz do projeto no Drive
- **THEN** a subpasta é criada antes do upload do arquivo

#### Scenario: Fallback sem credenciais Drive
- **WHEN** as credenciais Google Drive não estão configuradas (`DriveSetupError`)
- **THEN** o upload é pulado, o livreto local é preservado em `output/{job_id}/livreto.pdf`, e o resultado inclui `booklet_drive_url: null` com uma mensagem de aviso

#### Scenario: Falha de upload Drive
- **WHEN** o upload ao Drive falha por erro de rede ou quota
- **THEN** o erro é capturado, emitido como `type: log` de aviso, e o livreto local permanece disponível para download
