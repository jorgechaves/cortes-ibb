## Context

Já temos um pipeline (`video-cuts-ibb`) que recorta o vídeo em 6 trechos e um app (`video-cuts-app`) que orquestra tudo com barra de progresso. O ponto fraco identificado pelo operador é a **qualidade das escolhas**: cortar em pausas é necessário mas não suficiente. Precisamos garantir que cada corte:
- comece em uma "abertura" reconhecível,
- termine em uma "conclusão",
- expresse uma ideia auto-contida quando assistido sem o resto do vídeo,
- e que o conjunto dos 6 cubra momentos diferentes.

A transcrição word-level do faster-whisper já dá o material textual; a janela de pausas dá os pontos de corte mecânicos. Falta um juízo semântico — exatamente o tipo de tarefa onde um LLM pequeno (Haiku) brilha por custo/latência.

## Goals / Non-Goals

**Goals:**
- Selector híbrido: pausas dão candidatos, LLM escolhe os melhores 6.
- Manter o app 100% automático (sem revisão humana intermediária).
- Fallback robusto: se LLM/API indisponível, pipeline continua com heurística mais rígida e avisa a UI.
- Output enriquecido (title + rationale) que ajude o operador a entender as escolhas.

**Non-Goals:**
- Não usar LLM para gerar ou reescrever transcrição.
- Não embarcar modelos locais — fica como possibilidade futura, não nesta change.
- Não alterar render, legendas, ícone, outro ou upload — só a fase de seleção e o output mostrado na UI.

## Decisions

### Decisão 1: Modelo Claude API — `claude-haiku-4-5`
Haiku 4.5 dá custo/latência mínimos com qualidade suficiente para a tarefa de avaliar coerência semântica de trechos de ~60s. Uma única chamada com a transcrição completa + janelas-candidato cabe folgadamente em 20K tokens de entrada.

**Alternativa considerada:** Sonnet 4.6. Rejeitado porque a tarefa não exige raciocínio profundo — é uma escolha entre alternativas com critérios claros, onde Haiku já performa bem; custo cai ~5×.

### Decisão 2: Uma chamada única, não uma por candidato
Enviar todas as 12–20 janelas-candidato em uma chamada e pedir as 6 melhores. Evita N chamadas e permite ao modelo **comparar** candidatos diretamente, atendendo o critério de diversidade.

Formato do prompt (resumo):
```
System: Você seleciona trechos coerentes para clipes curtos em redes sociais.
User:
  Você verá <N> candidatos de trechos de 50–75s extraídos de uma palestra.
  Escolha os 6 melhores, otimizando para: (a) ideia completa, (b) abertura
  clara, (c) fechamento conclusivo, (d) valor isolado, (e) diversidade entre
  os 6. Retorne JSON com exatamente 6 itens em ordem cronológica.
  Candidatos: [{ "id": 1, "start": 12.3, "end": 71.5, "text": "..." }, ...]
```
Resposta esperada (validada contra JSON Schema):
```json
{
  "selections": [
    {"id": 3, "title": "...", "rationale": "...", "slug": "..."},
    ...
  ]
}
```
Usar `response_format=json_schema` para forçar saída válida.

### Decisão 3: Geração de candidatos
Algoritmo em `pipeline/selector.py`:
1. Da transcrição word-level, construir lista de "fronteiras candidatas" — toda pausa >700 ms.
2. Marcar quais fronteiras são **fortes** (a palavra anterior termina com `.`/`?`/`!`).
3. Enumerar pares (start_boundary, end_boundary) com:
   - `start_boundary` é fronteira forte (preferência) ou pausa simples (alternativa),
   - `end_boundary` é fronteira forte (obrigatório),
   - 50 ≤ (end − start) ≤ 75 s.
4. Filtrar para pegar no máximo 20 candidatos, preferindo distribuir ao longo da timeline (greedy: dividir o vídeo em 6 bins e pegar até 3–4 candidatos por bin).
5. Empacotar texto do trecho a partir da transcrição.

Se < 6 candidatos sobreviverem ao filtro (vídeo muito curto, pausas escassas), relaxar gradualmente: aceitar pausa >500 ms no end, depois fim sem pontuação final mas em pausa muito longa.

### Decisão 4: Validação da resposta do LLM
- Resposta DEVE ser JSON parseável; usar `json.loads`.
- DEVE conter exatamente 6 entradas.
- Cada entrada DEVE referenciar um `id` válido (presente nos candidatos enviados).
- IDs devem ser únicos.
- `title` ≤ 8 palavras, `rationale` ≤ 1 frase (cortar se necessário).
- Se qualquer validação falhar, tentar novamente uma vez (com `temperature` levemente menor); se falhar de novo, cair no fallback heurístico.

### Decisão 5: Fallback heurístico estrito
Quando `ANTHROPIC_API_KEY` está ausente OU a chamada falha:
1. Filtrar candidatos para apenas aqueles com fronteiras **fortes** (pontuação final no início e no fim).
2. Se houver ≥ 6, escolher 6 com maior espaçamento (distribuir uniformemente).
3. Se houver < 6, relaxar a fronteira inicial (aceitar pausa >700 ms sem pontuação) e tentar de novo.
4. Marcar `selection_mode='heuristic'` em todos os cortes; gerar slug a partir das palavras-chave (substantivos mais frequentes do trecho); deixar `rationale=None`.

### Decisão 6: Schema do `cuts.json`
```json
{
  "selection_mode": "semantic" | "heuristic",
  "model": "claude-haiku-4-5" | null,
  "fallback_reason": null | "missing_api_key" | "api_error: ...",
  "cuts": [
    {
      "idx": 1,
      "start": 12.3,
      "end": 71.5,
      "slug": "fe-e-obras",
      "title": "Fé sem obras é morta",
      "rationale": "Encerra com a aplicação prática para a vida.",
      "selection_mode": "semantic"
    }
  ]
}
```
Esse arquivo é consumido pelo render e pelo `report.md`.

### Decisão 7: Onde a chamada acontece
- Novo módulo `pipeline/semantic_selector.py` com `def choose(candidates, on_event) -> SelectionResult`.
- `pipeline/selector.py` continua gerando candidatos; `__init__.py` chama `semantic_selector.choose` em sequência.
- `on_event` recebe `progress` (3 valores: 0%, 50% durante chamada, 100% ao parsear).

### Decisão 8: SDK e configuração
- Pacote `anthropic>=0.40.0`.
- Cliente lazy-init em `semantic_selector.py`; lê `ANTHROPIC_API_KEY` do `os.environ`.
- Timeout: 30 s por chamada.
- Retry: 1 retentativa adicional em erros transientes (429, 5xx, timeout) via `client.with_options(max_retries=...)` ou loop manual.

### Decisão 9: UI — exibir rationale
- Adicionar `data-rationale` em cada item da lista; renderizar `<em>` abaixo do título.
- Quando `selection_mode === 'heuristic'`, renderizar banner `<div class="warning">` no topo da lista com o motivo.
- Sem mudanças na barra de progresso (estágio "seleção" já tem peso 3%).

## Risks / Trade-offs

- **API offline ou sem chave** → fallback heurístico ativa. Mitigação: o fallback ainda produz cortes utilizáveis; UI sinaliza claramente.
- **LLM retorna IDs inexistentes ou JSON malformado** → retry + fallback. Mitigação: validar contra os IDs enviados; segunda tentativa com `temperature=0`.
- **Custo escala se houver muitos vídeos por dia** → ~$0.01 por job é trivial; documentar para o operador.
- **Latência adicional 3–6 s** → cabe no estágio "seleção" (3% do total). Sem impacto perceptível.
- **Privacidade da transcrição** → o áudio transcrito vai para a Anthropic. Mitigação: documentar explicitamente no README; oferecer modo `--no-llm` (env var `DISABLE_SEMANTIC_SELECTION=1`) para sermões sensíveis.
- **Modelo preferindo trechos "espetaculosos" em detrimento dos teologicamente densos** → ajustar o prompt para penalizar isso; revisão do operador no início é recomendada nas primeiras execuções.

## Migration Plan

- `pipeline/selector.py` continua existindo, mas seu output passa a ser "candidatos" em vez de "6 escolhidos".
- Novo módulo `pipeline/semantic_selector.py` é chamado entre `selector` e `ass_builder`.
- `cuts.json` ganha campos novos (`title`, `rationale`, `selection_mode`); consumidores antigos (render) só leem `start`/`end`/`slug`, então a mudança é retrocompatível.
- Sem migração de arquivos existentes — o pipeline só roda novos jobs.

## Open Questions

- Quanto contexto do vídeo enviar além dos textos dos candidatos? Sugestão: enviar também um "resumo" de 200 caracteres do vídeo inteiro (primeiras 2 min + últimas 2 min concatenadas) para ajudar o modelo a entender o tema global. Decidir no PR de implementação.
- Aceitar override manual via env (`SELECTION_IDS=3,7,11,...`) para debug? Provavelmente útil; adicionar como tarefa.
