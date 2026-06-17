## 1. Dependências e configuração

- [x] 1.1 Adicionar `reportlab` ao `requirements.txt`
- [x] 1.2 Instalar `reportlab` no ambiente virtual (`.venv`) com `pip install reportlab`
- [x] 1.3 Adicionar `.pdf` ao dicionário `EXT_TO_MIME` em `pipeline/drive.py` com valor `"application/pdf"`

## 2. Módulo de geração de livreto

- [x] 2.1 Criar `pipeline/booklet.py` com função `correct_text(text: str, on_event) -> str` que envia o transcript ao OpenAI em chunks de até 1.500 palavras para corrigir PT-BR, com fallback para texto original em caso de erro
- [x] 2.2 Implementar `build_cover_page(canvas, page_size, icon_path, title)` em `pipeline/booklet.py` para renderizar capa A5 com `icone.png` centralizado e título abaixo do ícone
- [x] 2.3 Implementar `build_back_cover_page(canvas, page_size, icon_path)` em `pipeline/booklet.py` para renderizar contracapa A5 com `icone.png` centralizado
- [x] 2.4 Implementar `build_content_pages(doc, text)` em `pipeline/booklet.py` usando `SimpleDocTemplate` do ReportLab com página A5 (148×210mm), margens 15mm, fonte serifada 11pt, espaçamento 1.3×, texto justificado e numeração de página centralizada no rodapé
- [x] 2.5 Implementar função pública `generate_booklet(job_dir: str, icon_path: str, out_path: str, on_event) -> str` em `pipeline/booklet.py` que orquestra: leitura do `transcript.txt`, correção via OpenAI, montagem do PDF (capa + conteúdo + contracapa) e retorno do caminho do PDF gerado

## 3. Upload ao Google Drive (subpasta livros)

- [x] 3.1 Implementar função `upload_booklet_to_drive(pdf_path: str, on_event) -> dict | None` em `pipeline/booklet.py` que usa `pipeline/drive.py` para criar/obter a subpasta `livros/` dentro de `TARGET_FOLDER_ID` e faz upload do `livreto.pdf`

## 4. Rota API

- [x] 4.1 Adicionar rota `POST /booklet/{job_id}` em `app.py` que verifica existência de `output/{job_id}/transcript.txt`, retorna 404 se ausente, e dispara geração em thread separada com fila SSE própria
- [x] 4.2 Adicionar rota `GET /booklet/{job_id}/events` em `app.py` (ou reutilizar o padrão SSE existente) para transmitir eventos de progresso da geração do livreto
- [x] 4.3 Adicionar rota `GET /files/{job_id}/livreto.pdf` — verificar que a rota genérica `/files/{job_id}/{name}` existente já cobre o download do `livreto.pdf` (se sim, nenhuma mudança necessária)

## 5. Interface web

- [x] 5.1 Adicionar botão "Gerar Livreto" em `web/index.html` na seção de resultados, visível apenas quando `transcript_local_path` está presente no resultado do job
- [x] 5.2 Implementar handler JS em `web/index.html` que chama `POST /booklet/{jobId}`, consome SSE de progresso e exibe logs na área de log existente
- [x] 5.3 Exibir link de download do `livreto.pdf` e link do Drive (se `booklet_drive_url` presente) após conclusão bem-sucedida

## 6. Testes manuais

- [x] 6.1 Testar geração com um job existente que tenha `transcript.txt` (`output/<job_id>/transcript.txt`)
- [x] 6.2 Verificar visualmente que o PDF gerado segue o layout dos PDFs de referência em `ebook/` (capa, conteúdo, contracapa)
- [x] 6.3 Verificar que o arquivo `livreto.pdf` aparece na subpasta `livros/` no Google Drive
- [x] 6.4 Testar fallback: desativar `OPENAI_API_KEY` e verificar que o livreto é gerado com o texto original
- [x] 6.5 Testar fallback: remover credenciais Drive e verificar que o livreto local é preservado sem erro fatal
