# Spec: drive-upload

## Purpose

Gerencia o upload de arquivos para o Google Drive, incluindo o mapeamento de extensões para tipos MIME e a lógica de envio via `pipeline/drive.py`.

## Requirements

### Requirement: Suporte a MIME type PDF no mapeamento de extensões
O mapeamento `EXT_TO_MIME` em `pipeline/drive.py` SHALL incluir a extensão `.pdf` mapeada para `application/pdf`, permitindo que arquivos PDF sejam enviados ao Drive com o tipo MIME correto.

#### Scenario: Upload de PDF com tipo MIME correto
- **WHEN** `upload_file` é chamado com um arquivo de extensão `.pdf`
- **THEN** o arquivo é enviado ao Drive com `mimeType: "application/pdf"`
