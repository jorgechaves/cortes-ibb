## Why

O passo de melhoria de texto do livreto (`correct_text()` em `pipeline/booklet.py`) aplica apenas correção ortográfica e gramatical básica. A skill `/editor` (instalada em `.agents/skills/editor/SKILL.md`) define um conjunto mais completo de princípios de edição profissional — clareza, concisão, voz ativa, eliminação de redundâncias, coesão entre parágrafos — que, quando aplicados ao texto de um sermão transcrito, produzem um livreto muito mais legível e polido em português brasileiro.

## What Changes

- O prompt enviado ao OpenAI durante a geração do livreto é expandido para incorporar os princípios da skill `/editor` adaptados ao português brasileiro e ao gênero textual sermão/pregação.
- **BREAKING** O prompt deixa de ser apenas "corrija ortografia e gramática" e passa a ser uma edição completa: correção + melhoria de clareza + eliminação de redundâncias + conversão para voz ativa + fortalecimento de verbos + coesão entre parágrafos.
- A restrição "não resuma e não omita conteúdo" é mantida — o editor melhora a forma sem alterar a substância da mensagem.
- O nome interno da função `correct_text()` passa a `edit_text()` para refletir o escopo ampliado.
- A mensagem de progresso no log muda de "Corrigindo português brasileiro" para "Revisando e melhorando o texto".

## Capabilities

### New Capabilities

### Modified Capabilities
- `booklet-generator`: O prompt de edição de texto agora aplica os princípios da skill `/editor` (clareza, concisão, voz ativa, coesão) além da correção ortográfica. Requisito novo: o texto editado NÃO DEVE ser resumido nem ter conteúdo omitido.

## Impact

- `pipeline/booklet.py`: atualização do `SYSTEM` prompt em `correct_text()` / `edit_text()`, renomeação da função e das mensagens de log.
- `.agents/skills/editor/SKILL.md`: arquivo de referência (leitura apenas, sem modificação).
- Sem mudanças em `app.py`, `web/index.html` ou outros módulos.
