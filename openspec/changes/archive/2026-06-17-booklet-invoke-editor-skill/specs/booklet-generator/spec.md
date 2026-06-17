## MODIFIED Requirements

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
