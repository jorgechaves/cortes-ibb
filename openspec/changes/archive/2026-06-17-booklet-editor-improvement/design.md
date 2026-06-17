## Context

A skill `/editor` (`.agents/skills/editor/SKILL.md`) define quatro níveis de edição: proofreading, copy editing, line editing e developmental editing. Para um sermão transcrito em português brasileiro, os níveis mais relevantes são copy editing (escolha de palavras, eliminação de redundâncias) e line editing (fluxo, coesão entre parágrafos, ritmo). O nível developmental (reestruturação de argumentos) NÃO é aplicável pois não podemos alterar a sequência ou o conteúdo do sermão.

O passo de edição já usa OpenAI em chunks de 1.500 palavras. A mudança é exclusivamente no SYSTEM prompt — sem alteração de arquitetura, sem novas dependências.

## Goals / Non-Goals

**Goals:**
- Expandir o SYSTEM prompt para incluir os princípios da skill `/editor` adaptados ao PT-BR e ao gênero pregação/sermão
- Aplicar: eliminação de redundâncias, conversão de voz passiva para ativa, fortalecimento de verbos fracos, melhoria de coesão entre parágrafos, variação de estrutura de frases
- Manter a restrição absoluta: NÃO resumir, NÃO omitir, NÃO reordenar o conteúdo
- Atualizar nome da função e mensagens de log
- Adaptar os princípios ao contexto de sermão: preservar citações bíblicas literalmente, respeitar termos teológicos, não secularizar expressões religiosas

**Non-Goals:**
- Não aplicar developmental editing (reestruturação do argumento)
- Não usar a skill `/editor` como um agente separado — é incorporada como instruções ao OpenAI
- Não alterar o template visual do PDF
- Não criar uma nova chamada à API — é a mesma chamada com prompt expandido

## Decisions

### Prompt em português vs. inglês

O SYSTEM prompt será escrito em **português brasileiro** para maximizar a qualidade da edição — modelos de linguagem tendem a aplicar regras de estilo com mais precisão quando as instruções e o texto-alvo estão no mesmo idioma. A skill `/editor` original é em inglês, mas suas regras são traduzidas e adaptadas.

### Princípios incluídos (adaptados da skill /editor para PT-BR e sermão)

```
CORRIJA:
- Ortografia, acentuação e pontuação
- Concordância nominal e verbal

MELHORE (sem alterar o conteúdo):
- Elimine redundâncias e palavras desnecessárias
  ("devido ao fato de que" → "porque"; "a fim de" → "para")
- Converta voz passiva para ativa quando possível
- Fortaleça verbos fracos
  ("fazer uma decisão" → "decidir"; "ter a capacidade de" → "poder")
- Melhore a coesão entre parágrafos (conectivos, transições)
- Varie a estrutura das frases para evitar monotonia

PRESERVE SEMPRE:
- Citações bíblicas: reproduza literalmente
- Termos teológicos e expressões de fé
- A ordem e o conteúdo do argumento
- NÃO resuma, NÃO omita, NÃO reordene
```

### Renomeação da função

`correct_text()` → `edit_text()` para refletir o escopo ampliado. A interface pública (`generate_booklet()`, `upload_booklet_to_drive()`) não muda.

## Risks / Trade-offs

- **[Risco] Tokens por chunk aumentam com prompt mais longo (~50 tokens extras):** impacto desprezível em `gpt-4o-mini`. → Sem mitigação necessária.
- **[Risco] O modelo pode "resumir" mesmo instruído a não resumir:** o prompt reforça explicitamente a proibição. → Aceitável; a restrição já existia e funciona.
- **[Risco] Citações bíblicas podem ser "melhoradas" incorretamente:** instrução específica de preservar literalmente. → Mitigado.
- **[Trade-off] Melhoria de estilo vs. fidelidade à voz do pastor:** o editor pode tornar o texto mais formal do que a pregação original. Aceitável — o livreto é um documento escrito, não a transcrição literal da fala.
