## Why

Após gerar o transcript de um sermão (com cortes, com legenda, sem legenda ou somente transcrição), o conteúdo textual fica disponível em `transcript.txt` mas não há como transformá-lo em material imprimível. Pastores e colaboradores precisam de um livreto A5 formatado, com capa e contracapa, corrigido em português brasileiro, que possa ser distribuído fisicamente ou compartilhado como PDF.

## What Changes

- Nova etapa opcional na pipeline: após o processamento do vídeo, gerar um livreto A5 em PDF a partir do `transcript.txt` do job.
- O livreto usa `icone.png` na capa e contracapa, segue o layout dos PDFs existentes em `ebook/`, e corrige ortografia/concordância em português brasileiro (sem resumir o conteúdo).
- O PDF gerado é salvo na pasta do job (`output/<job_id>/livreto.pdf`).
- O livreto é enviado automaticamente ao Google Drive na subpasta `livros/` dentro da pasta-raiz do projeto Drive.
- Nova rota `POST /booklet/<job_id>` na API FastAPI para disparar a geração sob demanda.
- Botão "Gerar Livreto" na interface web, habilitado após a conclusão do processamento do vídeo (qualquer modo).

## Capabilities

### New Capabilities
- `booklet-generator`: Gera livreto A5 em PDF a partir de `transcript.txt`, aplicando correção de português brasileiro, capa/contracapa com `icone.png`, e layout baseado nos PDFs de referência do diretório `ebook/`.
- `booklet-drive-upload`: Envia o livreto PDF gerado ao Google Drive na subpasta `livros/` dentro da pasta raiz do Drive do projeto.

### Modified Capabilities
- `drive-upload`: Adição de suporte a subpasta `livros/` na função `get_or_create_folder` já existente em `pipeline/drive.py`.

## Impact

- Novo módulo `pipeline/booklet.py` com lógica de geração de PDF (ReportLab ou WeasyPrint).
- Nova rota `POST /booklet/{job_id}` em `app.py`.
- `pipeline/drive.py`: reutilização da função existente com subpasta `livros/`.
- `web/index.html`: botão "Gerar Livreto" na seção de resultados.
- Novas dependências Python: `reportlab` ou `weasyprint` (para PDF), `openai` (já presente, para correção PT-BR via LLM).
- Referência de layout: arquivos `ebook/Dominio_Proprio_Livreto.pdf` e `ebook/Nenhuma_Condenacao_Livreto.pdf`.
- Arquivo de ícone: `icone.png` na raiz do projeto.
