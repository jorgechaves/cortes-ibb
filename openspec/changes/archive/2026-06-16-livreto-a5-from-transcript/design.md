## Context

O projeto já transcreve áudio e grava `transcript.txt` em cada pasta de job (`output/<job_id>/`). O usuário quer que, após qualquer modo de processamento (cortes com/sem legenda ou somente transcrição), seja possível gerar um livreto A5 em PDF com o texto corrigido em português brasileiro, capa e contracapa com `icone.png`, seguindo o layout dos PDFs de referência em `ebook/`. O livreto deve ser enviado ao Google Drive na subpasta `livros/` dentro da pasta-raiz do projeto.

A infraestrutura de upload ao Drive já existe em `pipeline/drive.py` (`get_or_create_folder`, `upload_file`). A chave OpenAI já é usada para seleção semântica e pode ser reutilizada para a etapa de correção textual.

## Goals / Non-Goals

**Goals:**
- Gerar livreto A5 (148 × 210 mm) em PDF a partir de `transcript.txt` de um job existente
- Corrigir ortografia e concordância em português brasileiro via OpenAI (gpt-4o-mini), sem resumir o conteúdo
- Incluir capa e contracapa com `icone.png` centralizado, seguindo o layout dos PDFs de referência
- Salvar o PDF em `output/<job_id>/livreto.pdf`
- Fazer upload para Drive na subpasta `livros/` dentro da pasta-raiz (`TARGET_FOLDER_ID`)
- Expor rota `POST /booklet/{job_id}` com SSE para acompanhamento de progresso
- Adicionar botão "Gerar Livreto" na interface web após conclusão do job

**Non-Goals:**
- Geração automática do livreto junto com o processamento do vídeo (é sob demanda)
- Suporte a múltiplos formatos de saída (somente PDF)
- Extração de capítulos ou sumário automático
- Paginação inteligente com índice remissivo

## Decisions

### Biblioteca de PDF: ReportLab

**Escolha:** `reportlab` (já amplamente usada em Python para PDFs programáticos).

**Alternativa considerada:** `weasyprint` (renderização via HTML/CSS). Descartada porque exige instalação de dependências de sistema (Pango, Cairo) e é mais pesada para deploy simples.

`reportlab` permite controle preciso de layout: margens, fontes, tamanho de página A5, posicionamento de imagens — adequado para replicar o layout dos PDFs de referência.

### Correção PT-BR: OpenAI em chunks

O transcript pode ser longo (1h de sermão → ~10.000 palavras). A correção será feita em chunks de ~1.500 palavras via `gpt-4o-mini`, com prompt restritivo: "corrija apenas ortografia e concordância em português brasileiro, não resuma nem altere o conteúdo". Os chunks são processados sequencialmente e reunificados antes de montar o PDF.

**Alternativa considerada:** Correção local com `language_tool_python`. Descartada pela qualidade inferior em textos de pregação (vocabulário bíblico, termos evangélicos) e pelo fato de a chave OpenAI já estar presente.

### Estrutura do livreto

Baseada nos PDFs de referência em `ebook/` (A5, layout centrado, fonte serifada):
- **Capa**: página A5 com `icone.png` centralizado verticalmente, título extraído da primeira linha do transcript (ou nome do job como fallback)
- **Páginas de conteúdo**: margens 15mm, fonte DejaVu Serif 11pt (disponível via ReportLab), espaçamento 1.3×, texto justificado
- **Contracapa**: página A5 com `icone.png` centralizado

### Rota API e fluxo SSE

Nova rota `POST /booklet/{job_id}` em `app.py`. Retorna `StreamingResponse` com eventos SSE idênticos ao padrão já usado em `/events`. Não bloqueia o estado global (`JobState`) porque o booklet é pós-processamento de um job já concluído — usa um `threading.Thread` local com uma fila própria.

### Upload Drive

Reusa `pipeline/drive.py`. A subpasta `livros/` é criada via `get_or_create_folder(service, "livros", TARGET_FOLDER_ID)`. O arquivo `livreto.pdf` é enviado para essa subpasta.

## Risks / Trade-offs

- **Corpus longo → muitos tokens OpenAI** → Mitigação: chunks de 1.500 palavras com timeout de 60s por chunk; se falhar, usa o texto original sem correção.
- **ReportLab não inclui fonte serifada adequada por padrão** → Mitigação: usar `Helvetica` (embutida) ou registrar DejaVu Serif (open-source, incluída no pacote `reportlab`); validar visualmente contra PDFs de referência.
- **PDF muito grande se `icone.png` for de alta resolução** → Mitigação: redimensionar a imagem para 800px max antes de embutir no PDF.
- **Falha de Drive credentials** → Mitigação: já tratada em `drive.py` (`DriveSetupError`); o livreto local é preservado mesmo se o upload falhar.
- **Botão no UI aparece em jobs antigos que não têm `transcript.txt`** → Mitigação: o endpoint verifica se `transcript.txt` existe e retorna 404 antes de iniciar.

## Migration Plan

1. Instalar `reportlab` via `pip install reportlab` e adicionar em `requirements.txt`
2. Criar `pipeline/booklet.py` com funções `correct_text` e `build_pdf`
3. Adicionar rota `POST /booklet/{job_id}` em `app.py`
4. Atualizar `web/index.html` com botão "Gerar Livreto" (habilitado quando job tem `transcript.txt`)
5. Adicionar `.pdf` ao `EXT_TO_MIME` em `pipeline/drive.py`
6. Testar manualmente com um job existente que tenha `transcript.txt`

Rollback: remover a rota e o botão; `pipeline/booklet.py` é autônomo e não afeta o pipeline principal.

## Open Questions

- Qual fonte serifada usar para melhor fidelidade ao layout dos PDFs de referência? (a definir após inspeção visual com ReportLab)
- O título da capa deve ser editável pelo usuário via formulário, ou sempre extraído do transcript? (por ora: extraído automaticamente da primeira frase/linha)
