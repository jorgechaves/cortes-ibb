## Context

A skill `/editor` está em `.agents/skills/editor/SKILL.md` (212 linhas, ~3.500 tokens). O arquivo define os princípios de edição profissional que devem ser aplicados. A ideia é carregar esse arquivo em runtime e usá-lo como system prompt para Claude, em vez de manter uma cópia hardcoded no código Python.

O projeto já usa OpenAI (`openai>=1.50`) para seleção semântica de cortes e para edição do livreto. A adição do SDK Anthropic é nova dependência, mas o padrão de uso (chunks, fallback, on_event) permanece idêntico.

## Goals / Non-Goals

**Goals:**
- Carregar `.agents/skills/editor/SKILL.md` em runtime como system prompt para Claude
- Adicionar instrução de idioma PT-BR e restrições de sermão ao final do SKILL.md carregado
- Processar o transcript em chunks de 1.500 palavras via Anthropic API
- Implementar fallback em cascata: Anthropic → OpenAI → texto original
- Modelo configurável via `CLAUDE_MODEL` (default: `claude-haiku-4-5-20251001`)

**Non-Goals:**
- Não invocar a skill como CLI (`claude /editor`) — a integração é via API
- Não alterar o SKILL.md
- Não remover o suporte a OpenAI — permanece como fallback
- Não mudar o formato de output do livreto

## Decisions

### SDK Anthropic direto, não subprocess

**Escolha:** `anthropic` Python SDK com `client.messages.create()`.

**Alternativa descartada:** subprocess `claude --print /editor < chunk.txt`. Frágil, dependente de versão CLI, sem controle de timeout e sem acesso ao token streaming.

### Localização do SKILL.md

O caminho é resolvido relativamente à raiz do projeto:
```python
SKILL_PATH = Path(__file__).resolve().parents[1] / ".agents" / "skills" / "editor" / "SKILL.md"
```
Se o arquivo não existir, cai no fallback OpenAI com log de aviso.

### System prompt composto

```
{conteúdo do SKILL.md}

---
CONTEXTO ESPECÍFICO:
- Edite em português brasileiro.
- O texto é a transcrição de um sermão evangélico.
- Preserve citações bíblicas literalmente.
- NÃO resuma, NÃO omita, NÃO reordene o conteúdo.
- Ao identificar transição temática, prefixe com '## Título Breve' (máx 5 palavras).
- Retorne somente o texto editado, sem comentários nem resumo de alterações.
```

### Modelo padrão: claude-haiku-4-5-20251001

Edição de texto é uma tarefa de copy editing — não requer raciocínio profundo. Haiku é 10× mais rápido e econômico que Sonnet para este caso. Configurável via `CLAUDE_MODEL` para quem quiser Sonnet.

### Fallback em cascata

```
ANTHROPIC_API_KEY configurada + SKILL.md existe?
  → usa Claude com SKILL.md
  → se falhar: loga aviso, cai no OpenAI

OPENAI_API_KEY configurada?
  → usa OpenAI com prompt interno
  → se falhar: loga aviso, usa texto original

Nenhuma key configurada?
  → usa texto original, loga aviso
```

### Chunks e timeout

Mantém chunks de 1.500 palavras e timeout de 60s por chunk (mesmo padrão atual). A Anthropic API suporta requisições síncronas com `max_tokens=4096` suficiente para 1.500 palavras editadas.

## Risks / Trade-offs

- **[Risco] ANTHROPIC_API_KEY não configurada no .env:** o fallback para OpenAI funciona automaticamente. → Mitigado.
- **[Risco] SKILL.md removido ou movido:** log de aviso + fallback OpenAI. → Mitigado.
- **[Risco] Custo adicional:** Haiku é ~$0.00025/1K tokens. Um sermão de ~10.000 palavras ≈ 13.000 tokens ≈ $0.003. Negligenciável. → Aceitável.
- **[Trade-off] Dois providers no mesmo arquivo:** aumenta a complexidade do `edit_text()`. Mitigado pela clareza do fallback em cascata.
