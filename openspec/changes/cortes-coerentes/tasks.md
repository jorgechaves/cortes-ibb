## 1. Dependências e configuração

- [x] 1.1 Adicionar `anthropic>=0.40.0` ao `requirements.txt`
- [x] 1.2 Documentar `ANTHROPIC_API_KEY` no `README.md` (criação no console.anthropic.com, escopo, custo aproximado)
- [x] 1.3 Documentar a env opcional `DISABLE_SEMANTIC_SELECTION=1` para forçar fallback
- [x] 1.4 Documentar a env opcional `ANTHROPIC_MODEL=claude-haiku-4-5` (padrão), útil para testes com Sonnet

## 2. Geração de candidatos (`pipeline/selector.py`)

- [x] 2.1 Refatorar `selector.py` para deixar de retornar 6 cortes finais e passar a retornar até 20 candidatos
- [x] 2.2 Identificar fronteiras "fortes" (palavra anterior termina com `.`/`?`/`!`) e fronteiras simples (pausa >700 ms)
- [x] 2.3 Enumerar pares (start, end) com 50 ≤ duração ≤ 75 s, preferindo start/end fortes
- [x] 2.4 Distribuir candidatos em 6 bins temporais para garantir cobertura ao longo do vídeo (até 3–4 por bin)
- [x] 2.5 Anexar `text` (transcrição word-level concatenada) e `id` sequencial a cada candidato
- [x] 2.6 Teste unitário com fixtures sintéticas (palavras + timestamps fake) cobrindo: vídeo curto, vídeo longo, sem pausas fortes

## 3. Selector semântico (`pipeline/semantic_selector.py`)

- [x] 3.1 Criar módulo com `def choose(candidates, on_event, *, model=None, video_summary=None) -> SelectionResult`
- [x] 3.2 Inicializar cliente `anthropic.Anthropic()` lazy; ler `ANTHROPIC_API_KEY` do ambiente; respeitar `ANTHROPIC_MODEL`
- [x] 3.3 Montar prompt system + user com instruções, critérios (a–e) e os candidatos serializados em JSON
- [x] 3.4 Configurar `messages.create` com `response_format` JSON Schema exigindo 6 entradas (`id`, `title`, `rationale`, `slug`)
- [x] 3.5 Habilitar prompt caching no system prompt (instruções fixas) para reduzir custo em jobs sequenciais
- [x] 3.6 Timeout 30s; 1 retry adicional com `temperature=0` em caso de JSON inválido ou IDs fora do conjunto
- [x] 3.7 Emitir eventos `progress` (0% antes da chamada, 60% durante, 100% após parse)
- [x] 3.8 Validar resultado: 6 itens únicos, IDs válidos, `title` ≤ 8 palavras (trunca se passar), `rationale` ≤ 200 chars
- [x] 3.9 Em falha definitiva, levantar `SemanticSelectionFailure(reason)` para o orquestrador decidir o fallback

## 4. Fallback heurístico estrito (`pipeline/selector.py`)

- [x] 4.1 Função `pick_six_heuristic(candidates) -> list[CutMeta]` que filtra para fronteiras fortes e distribui 6
- [x] 4.2 Relaxamento progressivo se < 6 candidatos atendem o critério mais estrito
- [x] 4.3 Slug derivado de substantivos frequentes do trecho (filtrar stopwords PT-BR)
- [x] 4.4 Garantir que `rationale` fica `None` e `selection_mode='heuristic'`

## 5. Orquestração (`pipeline/__init__.py`)

- [x] 5.1 No estágio "seleção": chamar `selector.gather_candidates` → tentar `semantic_selector.choose` se key presente e `DISABLE_SEMANTIC_SELECTION` ausente → fallback se erro
- [x] 5.2 Logar `fallback_reason` legível: `missing_api_key`, `api_error: <classe>: <mensagem>`, `validation_failed`
- [x] 5.3 Ordenar os 6 escolhidos por `start` ascendente e atribuir `idx` 1–6
- [x] 5.4 Gravar `cuts.json` com schema novo (`selection_mode`, `model`, `fallback_reason`, `cuts[*]`)
- [x] 5.5 Atualizar `report.md` para incluir `title` e `rationale` por corte

## 6. App / UI (`app.py` + `web/index.html`)

- [x] 6.1 Encaminhar evento `selection_done` (ou os campos já dentro de `done`) com `selection_mode` + `fallback_reason` para a UI
- [x] 6.2 Renderizar `title` em negrito e `rationale` em itálico em cada linha de resultado
- [x] 6.3 Renderizar banner amarelo quando `selection_mode='heuristic'` com motivo legível
- [x] 6.4 Caso `ANTHROPIC_API_KEY` ausente no startup, exibir aviso suave (não bloqueante) na drop zone: "Modo semântico desativado — defina ANTHROPIC_API_KEY para cortes melhores"

## 7. Validação end-to-end

- [ ] 7.1 Com `ANTHROPIC_API_KEY` válida: rodar o vídeo real e verificar que os 6 cortes têm `title`, `rationale` e cobrem momentos distintos do vídeo
- [ ] 7.2 Inspecionar cada corte: começa em fronteira de frase, termina em fronteira de frase, transmite uma ideia auto-contida
- [ ] 7.3 Comparar com a versão heurística (forçar `DISABLE_SEMANTIC_SELECTION=1`) e julgar visivelmente a melhora
- [ ] 7.4 Simular falha de API (revogar key temporariamente) e confirmar fallback + banner amarelo
- [ ] 7.5 Confirmar que custo da chamada Claude ficou dentro de poucos centavos (ver `usage` no log)

## 8. Encerramento

- [x] 8.1 Atualizar `README.md` com a seção "Como a seleção funciona" explicando os dois modos
- [ ] 8.2 Marcar a change como pronta para `/opsx:archive` após o teste end-to-end aprovado
