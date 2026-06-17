## MODIFIED Requirements

### Requirement: Geração de livreto A5 em PDF a partir do transcript
O sistema SHALL gerar um arquivo PDF no formato A5 (148 × 210 mm) a partir do arquivo `transcript.txt` de um job existente, seguindo o template visual de `modelo_livreto.pdf`. O conteúdo textual SHALL ter ortografia e concordância corrigidas em português brasileiro antes de ser incluído no PDF. O sistema NÃO DEVE resumir, omitir ou reorganizar o conteúdo do transcript. O nome do arquivo PDF gerado SHALL ser `livreto-{titulo_slug}.pdf` quando `titulo.txt` existir no `job_dir`; caso contrário, SHALL ser `livreto.pdf`.

#### Scenario: Livreto gerado com título fornecido
- **WHEN** `POST /booklet/{job_id}` é chamado e `output/{job_id}/titulo.txt` existe com conteúdo "A Graça de Deus"
- **THEN** o sistema gera `output/{job_id}/livreto-a-graca-de-deus.pdf` com o título "A Graça de Deus" na capa e no cabeçalho das páginas de conteúdo

#### Scenario: Livreto gerado sem título (fallback)
- **WHEN** `POST /booklet/{job_id}` é chamado e `output/{job_id}/titulo.txt` não existe
- **THEN** o sistema gera `output/{job_id}/livreto.pdf` com o título extraído do transcript via `_extract_title()`, preservando o comportamento atual

#### Scenario: Livreto enviado ao Drive com nome correto
- **WHEN** o livreto é gerado com título "A Graça de Deus"
- **THEN** o arquivo enviado ao Drive/livros/ tem nome `livreto-a-graca-de-deus.pdf`

#### Scenario: Transcript não encontrado
- **WHEN** `POST /booklet/{job_id}` é chamado e `output/{job_id}/transcript.txt` não existe
- **THEN** a rota retorna HTTP 404 com mensagem `transcript.txt não encontrado para o job {job_id}`

#### Scenario: Job não existe
- **WHEN** `POST /booklet/{job_id}` é chamado com um `job_id` que não corresponde a nenhuma pasta em `output/`
- **THEN** a rota retorna HTTP 404

### Requirement: Capa seguindo o template modelo_livreto.pdf
O PDF gerado SHALL conter uma página de capa com: fundo azul-marinho (`#16243a`), barra dourada horizontal no topo e na base da página (~28pt de altura), barra vertical dourada à esquerda (~18pt de largura, entre as barras horizontais), `icone.png` no canto superior esquerdo (~30×30pt, abaixo da barra superior), título do sermão em fonte sem-serifa bold branca grande (~36pt), linha dourada horizontal após o título, e o texto "Pr. Carlos Chaves" no rodapé esquerdo em fonte sem-serifa branca. O título SHALL ser lido de `titulo.txt` quando disponível, e de `_extract_title()` como fallback.

#### Scenario: Capa com título de titulo.txt
- **WHEN** `titulo.txt` existe com conteúdo "Fé que Move Montanhas"
- **THEN** a capa exibe "Fé que Move Montanhas" como título grande em branco, sem depender de extração do transcript

#### Scenario: Capa com todos os elementos visuais
- **WHEN** o livreto é gerado
- **THEN** a primeira página exibe fundo `#16243a`, barras douradas topo e base, barra vertical dourada esquerda, ícone 30×30pt no topo-esquerdo, título grande branco, linha dourada separadora e "Pr. Carlos Chaves" no rodapé

#### Scenario: Título longo quebra em múltiplas linhas
- **WHEN** o título excede a largura disponível
- **THEN** o título é dividido em múltiplas linhas (word-wrap) mantendo-se dentro da área delimitada pela barra vertical e margem direita

### Requirement: Contracapa seguindo o template modelo_livreto.pdf
A última página do PDF SHALL ser uma contracapa com: fundo azul-marinho (`#16243a`), barras douradas horizontais idênticas à capa (topo e base), barra vertical dourada à esquerda, e `icone.png` centralizado na página (~100×100pt).

#### Scenario: Contracapa com ícone centralizado
- **WHEN** o livreto é gerado
- **THEN** a última página exibe fundo `#16243a`, barras douradas topo e base, barra vertical dourada esquerda, e `icone.png` centralizado horizontalmente e verticalmente na página

### Requirement: Páginas de conteúdo seguindo o template modelo_livreto.pdf
As páginas de conteúdo SHALL ter: fundo branco, cabeçalho com o título do sermão em cinza (~8.5pt Helvetica) seguido de linha dourada horizontal imediatamente abaixo, corpo de texto em Times-Roman 11pt preto justificado com leading 14.3pt e espaçamento entre parágrafos, número de página centralizado no rodapé em cinza. O título usado no cabeçalho SHALL ser o mesmo da capa (lido de `titulo.txt` ou extraído por fallback).

#### Scenario: Cabeçalho e corpo corretos em cada página
- **WHEN** o livreto é gerado e tem múltiplas páginas de conteúdo
- **THEN** cada página de conteúdo exibe o cabeçalho cinza + linha dourada no topo, texto do corpo justificado nas margens definidas, e número de página no rodapé

#### Scenario: Títulos de seção renderizados quando presentes no texto
- **WHEN** o texto corrigido contém um bloco iniciado por `## Título da Seção`
- **THEN** esse bloco é renderizado como texto teal (~15pt, Helvetica-Bold) seguido de linha dourada horizontal, sem ser incluído como parágrafo de corpo

#### Scenario: Texto sem títulos de seção flui como parágrafos puros
- **WHEN** o texto corrigido não contém nenhum marcador `##`
- **THEN** todo o conteúdo é renderizado como parágrafos de corpo sem interrupção

### Requirement: Correção de português brasileiro com detecção opcional de seções
O sistema SHALL editar o transcript em chunks de até 1.500 palavras usando a skill `/editor` carregada do arquivo `.agents/skills/editor/SKILL.md` como system prompt para Claude (Anthropic API). O system prompt SHALL ser composto pelo conteúdo do SKILL.md mais instruções adicionais de idioma PT-BR, preservação de citações bíblicas, proibição de resumo/omissão, e detecção de seções com `## Título Breve`. Se `ANTHROPIC_API_KEY` não estiver configurada ou o SKILL.md não for encontrado, o sistema SHALL usar OpenAI como fallback com o prompt interno atual. Se OpenAI também falhar, o sistema SHALL usar o texto original. O modelo Claude SHALL ser configurável via variável de ambiente `CLAUDE_MODEL` (default: `claude-haiku-4-5-20251001`).

#### Scenario: Edição via skill /editor com Claude
- **WHEN** `ANTHROPIC_API_KEY` está configurada e `.agents/skills/editor/SKILL.md` existe
- **THEN** o texto é editado por Claude usando o SKILL.md como system prompt, e o log exibe "Usando skill /editor via Claude (claude-haiku-4-5-20251001)"

#### Scenario: SKILL.md não encontrado — fallback para OpenAI
- **WHEN** `ANTHROPIC_API_KEY` está configurada mas o arquivo SKILL.md não existe no caminho esperado
- **THEN** o sistema loga "SKILL.md não encontrado — usando OpenAI como fallback" e processa via OpenAI

#### Scenario: Fallback para OpenAI quando Anthropic falha
- **WHEN** `ANTHROPIC_API_KEY` está configurada, SKILL.md existe, mas a chamada à API Anthropic falha
- **THEN** o chunk falho é inserido sem edição, o log registra o erro, e o processamento continua com os demais chunks

#### Scenario: Fallback para texto original sem nenhuma key
- **WHEN** nem `ANTHROPIC_API_KEY` nem `OPENAI_API_KEY` estão configuradas
- **THEN** o texto original é usado sem modificação e o log exibe "Nenhuma API configurada — usando texto original"

#### Scenario: Modelo configurável via CLAUDE_MODEL
- **WHEN** a variável de ambiente `CLAUDE_MODEL` está definida (ex: `claude-sonnet-4-6`)
- **THEN** esse modelo é usado em vez do default `claude-haiku-4-5-20251001`

#### Scenario: Seções identificadas pelo Claude
- **WHEN** Claude identifica transições temáticas no sermão
- **THEN** o texto retornado contém marcadores `## Título Breve` que são renderizados como títulos de seção teal no PDF

#### Scenario: Texto retornado com edição profissional completa
- **WHEN** OPENAI_API_KEY está configurada e o sermão tem redundâncias, voz passiva ou verbos fracos
- **THEN** o texto resultante tem clareza melhorada, redundâncias eliminadas e voz ativa, mantendo todo o conteúdo original

#### Scenario: Citações bíblicas preservadas literalmente
- **WHEN** o transcript contém citações de versículos bíblicos (ex: "Portanto agora nenhuma condenação há...")
- **THEN** a citação aparece no livreto sem alteração, mesmo que o editor melhore o texto ao redor

#### Scenario: Texto retornado com seções identificadas
- **WHEN** o OpenAI identifica transições temáticas e insere marcadores `##`
- **THEN** o PDF renderiza esses blocos como títulos de seção teal com linha dourada

#### Scenario: Fallback sem API key
- **WHEN** OPENAI_API_KEY não está configurada
- **THEN** o texto original é usado sem correção nem marcadores de seção, e o log exibe "OPENAI_API_KEY ausente — usando texto original"

#### Scenario: Fallback por erro de chunk
- **WHEN** a chamada à API OpenAI falha para um chunk específico
- **THEN** o chunk original é inserido sem edição, o processamento continua com os chunks seguintes, e o log registra o erro do chunk

#### Scenario: Mensagem de progresso no log
- **WHEN** a edição começa
- **THEN** o log exibe "Revisando e melhorando o texto em português brasileiro"

### Requirement: Botão "Gerar Livreto" na interface web
A interface web SHALL exibir um botão "Gerar Livreto" na seção de resultados após a conclusão de qualquer job que produza `transcript.txt`. O botão SHALL disparar `POST /booklet/{job_id}` e exibir progresso via SSE na mesma área de log.

#### Scenario: Botão habilitado após job concluído
- **WHEN** o job termina com status `done` e o resultado inclui `transcript_local_path`
- **THEN** o botão "Gerar Livreto" é exibido e clicável na seção de resultados

#### Scenario: Estado de carregamento durante geração
- **WHEN** o usuário clica em "Gerar Livreto"
- **THEN** o botão fica desabilitado e a área de log exibe eventos de progresso em tempo real

#### Scenario: Conclusão da geração
- **WHEN** a geração do livreto termina com sucesso
- **THEN** a interface exibe um link para download do PDF (com nome correto incluindo o título) e um link para o Drive (se disponível)
