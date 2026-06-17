## Why

O livreto gerado atualmente (`pipeline/booklet.py`) usa um layout simples com fundo escuro, `icone.png` centralizado e texto em Times-Roman — não segue o template visual da IBB definido em `modelo_livreto.pdf`. O objetivo é refazer o layout para que os livretos gerados sejam visualmente idênticos ao modelo: capa em azul-marinho com barras douradas, tipografia editorial, cabeçalho dourado nas páginas de conteúdo.

## What Changes

- **BREAKING** `generate_booklet()` em `pipeline/booklet.py`: redesign completo da função de geração de PDF para seguir o template `modelo_livreto.pdf` em vez do layout escuro atual.
- Capa: fundo azul-marinho (`#16243a`), barras douradas horizontais (topo e rodapé da página), barra vertical dourada à esquerda, `icone.png` pequeno no canto superior esquerdo, título grande em branco, linha dourada separadora, campo de pastor/autor no rodapé.
- Contracapa: espelha a capa — mesmo fundo azul-marinho, mesmas barras douradas, `icone.png` centralizado (maior, sem texto de título).
- Páginas de conteúdo: fundo branco, cabeçalho cinza com linha dourada, texto do corpo em fonte serifada 11pt justificado, numeração de página no rodapé.
- Detecção opcional de seções: o passo de correção via OpenAI tentará identificar transições naturais no sermão e inserir títulos de seção (`## Título`) derivados do próprio texto. Esses títulos são renderizados em teal com linha dourada, como no modelo. Se a IA não identificar seções, o texto flui como parágrafos puros — sem invenção de conteúdo.
- Paleta de cores extraída do `modelo_livreto.pdf`: azul-marinho `#16243a`, dourado `#c4963a`, teal para títulos de seção `#4a90a4`.

## Capabilities

### New Capabilities

### Modified Capabilities
- `booklet-generator`: **BREAKING** — requisito visual muda completamente. O PDF gerado SHALL seguir o template `modelo_livreto.pdf` (capa azul-marinho com barras douradas e `icone.png`, páginas de conteúdo com cabeçalho dourado e tipografia editorial). O comportamento de geração e upload ao Drive permanece inalterado.

## Impact

- `pipeline/booklet.py`: reescrita completa da lógica de renderização PDF (funções de capa, contracapa, cabeçalho, estilos de parágrafo e de seção).
- `modelo_livreto.pdf`: arquivo de referência — apenas leitura/consulta, sem modificação.
- `icone.png`: usado na capa (pequeno, canto superior esquerdo) e na contracapa (centralizado, maior).
- Sem mudanças em `app.py`, `web/index.html` ou `pipeline/drive.py`.
