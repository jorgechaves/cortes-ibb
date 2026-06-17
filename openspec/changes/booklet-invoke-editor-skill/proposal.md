## Why

O passo de edição do livreto (`edit_text()` em `pipeline/booklet.py`) usa a API OpenAI com um prompt que replica manualmente os princípios da skill `/editor`. O usuário quer que a skill `/editor` seja invocada de verdade — carregando o arquivo `SKILL.md` em tempo de execução e passando seu conteúdo como system prompt para um agente Claude (Anthropic API), que é o modelo para o qual a skill foi projetada. Isso garante que qualquer atualização futura da skill seja automaticamente refletida na edição do livreto.

## What Changes

- **BREAKING** `edit_text()` em `pipeline/booklet.py`: substituição da chamada OpenAI por chamada à API Anthropic (SDK `anthropic`), usando o conteúdo de `.agents/skills/editor/SKILL.md` como system prompt.
- O conteúdo do SKILL.md é lido em tempo de execução (não hardcoded), com instrução adicional de idioma: "Edite em português brasileiro. Preserve o conteúdo sem resumir."
- Nova dependência: `anthropic>=0.40` adicionada ao `requirements.txt`.
- Nova variável de ambiente necessária: `ANTHROPIC_API_KEY` (adicionada ao `.env.example`).
- Fallback: se `ANTHROPIC_API_KEY` não estiver configurada ou a skill SKILL.md não for encontrada, o sistema usa o comportamento anterior (OpenAI). Se OpenAI também não estiver configurada, usa o texto original.
- O modelo Claude usado é configurável via variável `CLAUDE_MODEL` (default: `claude-haiku-4-5-20251001` — rápido e econômico para edição de texto).

## Capabilities

### New Capabilities

### Modified Capabilities
- `booklet-generator`: O passo de edição de texto passa a usar a skill `/editor` via Anthropic API (Claude), com o SKILL.md como system prompt em tempo de execução. Fallback para OpenAI se Anthropic não disponível.

## Impact

- `pipeline/booklet.py`: `edit_text()` — troca de provider (OpenAI → Anthropic) com fallback em cascata.
- `requirements.txt`: adicionar `anthropic>=0.40`.
- `.env.example`: adicionar `ANTHROPIC_API_KEY=`.
- `.agents/skills/editor/SKILL.md`: lido em runtime, não modificado.
- Sem mudanças em `app.py`, `web/index.html` ou outros módulos.
