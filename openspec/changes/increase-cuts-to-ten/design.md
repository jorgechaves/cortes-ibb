## Context

O pipeline Cortes IBB gera cortes de vídeo em dois estágios principais: seleção (candidate generation + semantic/heuristic picker) e renderização. Atualmente, todos os estágios assumem exatamente **6 cortes** como constante implícita. A lógica de upload para o Google Drive nomeia a subpasta com a data do dia (`[2026-06-11]`), sem relação com o job em andamento.

Estado atual das constantes relevantes:
- `selector.gather_candidates`: distribuição em **6 bins**, cap 50 candidatos
- `semantic_selector`: schema `minItems: 12, maxItems: 18`; greedy target = 6
- `instagram.py`: schema `minItems/maxItems: 6`
- `drive.upload_all`: subfolder = `[datetime.now().strftime('%Y-%m-%d')]`

## Goals / Non-Goals

**Goals:**
- Aumentar o número de cortes gerados de 6 para 10 em todos os módulos do pipeline
- Nomear a subpasta no Google Drive com o `job_id` (nome da pasta de output, ex: `20260611-104011-9259`)

**Non-Goals:**
- Tornar o número de cortes configurável pelo usuário (UI ou env var) — escopo futuro
- Alterar a duração alvo dos cortes (60–180s permanece)
- Modificar o schema de saída do Drive além da renomeação da pasta

## Decisions

### 1. Bins do gerador de candidatos: 6 → 10
O `gather_candidates` distribui candidatos em `N` bins ao longo do vídeo para garantir cobertura temporal. Aumentar para 10 bins alinha a distribuição com o novo alvo. O `per_bin = ceil(50/10) = 5`, mantendo o cap total em 50.

_Alternativa considerada_: manter 6 bins e deixar o LLM cobrir o vídeo todo. Rejeitado — o bin-distribution garante cobertura mesmo em vídeos com regiões menos densas em pausas.

### 2. Seletor semântico: schema e greedy target
- `minItems`: 12 → 18 (garante buffer suficiente para 10 não-sobrepostos)
- `maxItems`: 18 → 24 (mais opções para cobrir o vídeo inteiro)
- `_greedy_nonoverlap` target: 6 → 10
- Prompt: "6 candidatos" → "10 candidatos"

_Alternativa_: aumentar apenas o `maxItems`. Rejeitado — com `minItems` baixo o LLM tende a retornar menos itens.

### 3. Seletor heurístico: `pick_six_heuristic` → `pick_n_heuristic(n=10)`
Renomear a função mantém o código legível. O `n` padrão é 10.

### 4. Instagram: schema 6 → 10
`minItems/maxItems` no JSON schema e validação interna passam de 6 para 10. O model context (gpt-4o-mini) suporta os ~15k tokens de 10 cortes sem problema.

### 5. Drive: nome da pasta = job_id
`upload_all` já recebe `out_dir`. Substituir `datetime.now().strftime(...)` por `Path(out_dir).name` dá o job_id (`20260611-104011-9259`) como nome da subpasta. Isso correlaciona diretamente os arquivos no Drive com a pasta local, facilitando rastreamento.

_Alternativa_: usar a data atual formatada diferente (ex: `2026-06-11-104011`). Rejeitado — o job_id já é único, inclui data e hora, e é o identificador canônico do run.

## Risks / Trade-offs

- **Custo de API aumenta ~67%** (10 vs 6 cortes × Instagram) — aceitável para o caso de uso de uma única palestra semanal.
- **Tempo de renderização aumenta ~67%** — vídeos de 90 min podem levar 15–20 min em vez de 10. Não há mudança arquitetural necessária (pipeline já é streaming com SSE).
- **Drive: pasta antiga** — jobs existentes no Drive usarão a nova convenção somente nos próximos runs. Pastas antigas com data permanecem intactas (sem migração).
- **Vídeos curtos**: fallback de 45s min pode não encontrar 10 candidatos em vídeos de < 15 min. O pipeline já loga avisos e o heurístico completa o que conseguir — comportamento correto.
