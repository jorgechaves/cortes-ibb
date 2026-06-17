## MODIFIED Requirements

### Requirement: Geração de livreto A5 em PDF a partir do transcript
O sistema SHALL gerar um arquivo PDF no formato A5 (148 × 210 mm) a partir do arquivo `transcript.txt` de um job existente, seguindo o template visual de `modelo_livreto.pdf`. O conteúdo textual SHALL ter ortografia e concordância corrigidas em português brasileiro antes de ser incluído no PDF. O sistema NÃO DEVE resumir, omitir ou reorganizar o conteúdo do transcript.

#### Scenario: Livreto gerado com sucesso seguindo o modelo
- **WHEN** `POST /booklet/{job_id}` é chamado e `output/{job_id}/transcript.txt` existe
- **THEN** o sistema gera `output/{job_id}/livreto.pdf` com capa azul-marinho, barras douradas, `icone.png` no topo-esquerdo da capa, páginas de conteúdo brancas com cabeçalho cinza + linha dourada, e contracapa azul-marinho com `icone.png` centralizado

#### Scenario: Transcript não encontrado
- **WHEN** `POST /booklet/{job_id}` é chamado e `output/{job_id}/transcript.txt` não existe
- **THEN** a rota retorna HTTP 404 com mensagem `transcript.txt não encontrado para o job {job_id}`

### Requirement: Capa seguindo o template modelo_livreto.pdf
O PDF gerado SHALL conter uma página de capa com: fundo azul-marinho (`#16243a`), barra dourada horizontal no topo e na base da página (~28pt de altura), barra vertical dourada à esquerda (~18pt de largura, entre as barras horizontais), `icone.png` no canto superior esquerdo (~30×30pt, abaixo da barra superior), título do sermão em fonte sem-serifa bold branca grande (~36pt), linha dourada horizontal após o título, e o texto "Pr. Carlos Chaves" no rodapé esquerdo em fonte sem-serifa branca.

#### Scenario: Capa com todos os elementos visuais
- **WHEN** o livreto é gerado
- **THEN** a primeira página exibe fundo `#16243a`, barras douradas topo e base, barra vertical dourada esquerda, ícone 30×30pt no topo-esquerdo, título grande branco, linha dourada separadora e "Pr. Carlos Chaves" no rodapé

#### Scenario: Título longo quebra em múltiplas linhas
- **WHEN** o título extraído do transcript excede a largura disponível
- **THEN** o título é dividido em múltiplas linhas (word-wrap) mantendo-se dentro da área delimitada pela barra vertical e margem direita

### Requirement: Páginas de conteúdo seguindo o template modelo_livreto.pdf
As páginas de conteúdo SHALL ter: fundo branco, cabeçalho com texto `{título} I {referência}` em cinza (~8.5pt Helvetica) seguido de linha dourada horizontal imediatamente abaixo, corpo de texto em Times-Roman 11pt preto justificado com leading 14.3pt e espaçamento entre parágrafos, número de página centralizado no rodapé em cinza.

#### Scenario: Cabeçalho e corpo corretos em cada página
- **WHEN** o livreto é gerado e tem múltiplas páginas de conteúdo
- **THEN** cada página de conteúdo exibe o cabeçalho cinza + linha dourada no topo, texto do corpo justificado nas margens definidas, e número de página no rodapé

#### Scenario: Títulos de seção renderizados quando presentes no texto
- **WHEN** o texto corrigido contém um bloco iniciado por `## Título da Seção`
- **THEN** esse bloco é renderizado como texto teal (~15pt, Helvetica-Bold) seguido de linha dourada horizontal, sem ser incluído como parágrafo de corpo

#### Scenario: Texto sem títulos de seção flui como parágrafos puros
- **WHEN** o texto corrigido não contém nenhum marcador `##`
- **THEN** todo o conteúdo é renderizado como parágrafos de corpo sem interrupção

### Requirement: Contracapa seguindo o template modelo_livreto.pdf
A última página do PDF SHALL ser uma contracapa com: fundo azul-marinho (`#16243a`), barras douradas horizontais idênticas à capa (topo e base), barra vertical dourada à esquerda, e `icone.png` centralizado na página (~100×100pt).

#### Scenario: Contracapa com ícone centralizado
- **WHEN** o livreto é gerado
- **THEN** a última página exibe fundo `#16243a`, barras douradas topo e base, barra vertical dourada esquerda, e `icone.png` centralizado horizontalmente e verticalmente na página

### Requirement: Correção de português brasileiro com detecção opcional de seções
O sistema SHALL enviar o transcript ao OpenAI em chunks de até 1.500 palavras para corrigir ortografia e concordância em português brasileiro. O prompt SHALL instruir o modelo a identificar transições temáticas naturais no sermão e a prefixar o primeiro parágrafo de cada nova seção com `## Título Breve` (máximo 5 palavras extraídas do conteúdo que se segue). Se nenhuma seção natural for identificada, o texto deve ser retornado sem marcadores `##`. Se a correção falhar, o sistema SHALL usar o texto original sem correção.

#### Scenario: Texto retornado com seções identificadas
- **WHEN** o OpenAI identifica transições temáticas e insere marcadores `##`
- **THEN** o PDF renderiza esses blocos como títulos de seção teal com linha dourada

#### Scenario: Fallback sem API key
- **WHEN** OPENAI_API_KEY não está configurada
- **THEN** o texto original é usado sem correção nem marcadores de seção

#### Scenario: Fallback por erro de chunk
- **WHEN** a chamada à API OpenAI falha para um chunk
- **THEN** o chunk original é usado e o processamento continua com os chunks seguintes
