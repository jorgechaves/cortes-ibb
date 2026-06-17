## Context

`pipeline/booklet.py` foi criado na mudança anterior (`livreto-a5-from-transcript`) com um layout próprio — fundo escuro, `icone.png` centralizado em capa e contracapa, corpo em Times-Roman simples. O `modelo_livreto.pdf` na raiz do projeto define um template editorial bem diferente, usado nos livros da IBB: azul-marinho com barras douradas na capa, tipografia limpa nas páginas de conteúdo.

O arquivo `modelo_livreto.pdf` foi gerado com ReportLab (confirmado pelo pdfinfo: "Producer: ReportLab PDF Library"). Isso significa que o projeto já usa a mesma biblioteca e não há diferença de toolchain — é uma reescrita de layout, não de dependências.

## Goals / Non-Goals

**Goals:**
- Reescrever `generate_booklet()` para produzir PDF visualmente idêntico ao `modelo_livreto.pdf`
- Capa: fundo azul-marinho, barras douradas horizontais (topo e base), barra vertical dourada à esquerda, `icone.png` no topo-esquerdo, título grande em branco, linha dourada, campo de autor no rodapé
- Contracapa: mesmo fundo/barras, `icone.png` centralizado (maior)
- Páginas de conteúdo: fundo branco, cabeçalho com título+linha dourada, parágrafo justificado, numeração de página
- Suporte opcional a títulos de seção (`## Heading` no texto) renderizados em teal com linha dourada, compatíveis com o estilo do modelo
- O passo de correção OpenAI pode opcionalmente detectar e inserir títulos de seção — se não detectar, tudo flui como corpo de texto

**Non-Goals:**
- Não alterar `app.py`, `web/index.html`, rotas ou lógica de upload ao Drive
- Não incluir campo de "Texto Base" ou referência bíblica automaticamente (o transcript não tem essa estrutura)
- Não implementar layout de duas colunas ou tabelas
- Não adicionar nova dependência além das já existentes (ReportLab já disponível)

## Decisions

### Paleta de cores extraída do modelo_livreto.pdf

Medidas visuais das screenshots e consistência com a variável CSS do app:

| Token | Hex | Uso |
|---|---|---|
| `NAVY` | `#16243a` | Fundo da capa e contracapa |
| `GOLD` | `#c4963a` | Barras, linha separadora, linha de seção |
| `TEAL` | `#4a90a4` | Texto de cabeçalho de seção |
| `GRAY_HEADER` | `#888888` | Texto de cabeçalho nas páginas de conteúdo |
| `BODY_TEXT` | `#1a1a1a` | Texto do corpo |

### Estrutura de página (BaseDocTemplate com PageTemplates)

Mantém a abordagem da implementação anterior — `BaseDocTemplate` com três `PageTemplate`s:
- `cover`: callback `on_cover` desenha fundo + barras + ícone + título
- `content`: callback `on_content` desenha cabeçalho cinza + linha dourada + número de página
- `back_cover`: callback `on_back_cover` desenha fundo + barras + ícone centralizado

**Alternativa descartada:** gerar páginas separadas e mesclar com PyPDF. Mais complexo sem vantagem.

### Dimensões da capa (medidas no modelo_livreto.pdf — A5 = 419×595 pt)

- Barra dourada superior: `rect(0, page_h - 28, page_w, 28)` → ~10mm de altura
- Barra dourada inferior: `rect(0, 0, page_w, 28)` → ~10mm de altura
- Barra vertical dourada esquerda: `rect(0, 28, 18, page_h - 56)` → ~6mm de largura, entre as barras horizontais
- `icone.png` no topo-esquerdo: 30×30pt, posicionado em `(30, page_h - 65)` (abaixo da barra dourada, alinhado à barra vertical)
- Bloco de título: começa em `x = 36` (à direita da barra vertical), `y ≈ page_h * 0.45`, fonte `Helvetica-Bold` 36pt branca
- Linha dourada sob o título: `rect(36, title_y - 8, page_w - 50, 1.5)` — largura quase total da página
- Campo de autor no rodapé: `(36, 52)`, `Helvetica` 12pt branca

### Detecção de seções via OpenAI (opcional)

O prompt de correção ganha instrução adicional: identificar transições temáticas naturais no sermão e prefixar o parágrafo com `## Título Breve` (máx 5 palavras, derivado do conteúdo que se segue). O gerador de PDF:
- Divide o texto em `\n\n`
- Se um bloco começa com `## `, renderiza como título de seção (teal, 15pt, + linha dourada) e o restante como corpo
- Caso contrário, renderiza como parágrafo normal

Isso respeita a restrição "não resuma" pois as palavras do título são extraídas do texto existente.

### Fonte do título na capa

O modelo usa aparentemente `Helvetica-Bold` (ou similar sem-serifa) para o título grande. ReportLab tem `Helvetica-Bold` embutido. Para o corpo, `Times-Roman` (serifada, embut).

**Alternativa:** registrar fontes externas. Descartada — complexidade desnecessária; as fontes embutidas do ReportLab são suficientes para fidelidade visual.

### Campo "Pr. Carlos Chaves" e "IBB — Igreja Batista Belém"

Esses campos são constantes do template IBB. Serão valores fixos (strings) no código, facilmente alteráveis. Não serão expostos como parâmetros configuráveis nesta mudança.

## Risks / Trade-offs

- **[Risco] Tamanho do `icone.png`:** icones PNG grandes podem aumentar muito o PDF. → Mitigação: redimensionar para no máximo 80pt antes de embutir, usando `drawImage` com `width`/`height` fixos.
- **[Risco] Detecção de seções pelo OpenAI pode ser inconsistente:** respostas variam. → Mitigação: o gerador de PDF trata `## Heading` como hint opcional; se não encontrar nenhum, funciona como texto puro.
- **[Risco] Cor exata da barra e do teal:** medida visualmente, pode não ser pixel-perfect. → Aceitável para um template editorial; pode ser ajustada após inspeção visual do PDF gerado.

## Migration Plan

1. Reescrever `pipeline/booklet.py` mantendo as assinaturas públicas: `correct_text`, `generate_booklet`, `upload_booklet_to_drive`
2. Testar localmente com transcript existente (`output/20260616-125521-0cdc/transcript.txt`)
3. Comparar PDF gerado com `modelo_livreto.pdf` visualmente
4. Nenhuma mudança em outros arquivos

Rollback: reverter `pipeline/booklet.py` para a versão anterior (o Git preserva o histórico).
