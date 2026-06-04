## Why

A seleção atual (heurística por pausa >500 ms) produz trechos com **timing tecnicamente limpo**, mas sem garantia de **coerência semântica**: um corte pode começar no meio de uma ideia, terminar antes da conclusão, ou pegar 60s que isoladamente não comunicam nada. Para o público das redes sociais da IBB, cada corte precisa funcionar como uma micro-mensagem com começo, meio e fim. "Os cortes devem fazer sentido" exige um avaliador semântico, não só temporal.

## What Changes

- Substituir a seleção puramente por pausas por um **selector híbrido em duas fases**:
  1. **Fase candidata (local, rápida)**: gerar 12–20 janelas-candidato de 50–75 s, ancoradas em pausas longas (>700 ms) e em pontuação final detectada na transcrição (`.`, `?`, `!`).
  2. **Fase semântica (LLM)**: enviar o texto de cada candidato para o Claude API (`claude-haiku-4-5`) com prompt estruturado para receber, em uma única chamada, os **6 melhores** trechos avaliados por: ideia completa, abertura clara, fechamento conclusivo, valor isolado, diversidade temática entre os 6.
- Adicionar **score e justificativa** por trecho ao mapa final de cortes (`cuts.json`): `{idx, start, end, slug, title, score, rationale}`.
- Adicionar fallback determinístico quando `ANTHROPIC_API_KEY` está ausente OU a chamada à API falha: usar uma heurística mais rígida (pausa >700 ms + pontuação final + abertura em início de frase), com aviso na UI de que o modo semântico está desativado.
- Atualizar a UI para exibir, ao final, **título curto e rationale** de cada corte na lista de resultados, ajudando o operador a entender por que cada trecho foi escolhido.
- Garantir **diversidade temática**: os 6 trechos finais SHALL cobrir momentos diferentes do vídeo (não amontoar em uma janela curta) e abordar tópicos distintos quando o conteúdo permitir.

## Capabilities

### New Capabilities
<!-- nenhuma capability nova; apenas modificações -->

### Modified Capabilities
- `video-cuts-ibb`: o requisito "Seleção dos 6 cortes" muda de "começa/termina em pausa" para "começa/termina em pausa **E** forma uma unidade semântica completa, validada por LLM". Adiciona campos no metadado de cada corte.
- `video-cuts-app`: o estágio `seleção dos cortes` passa a incluir chamada externa (LLM); a UI passa a exibir título + rationale por corte ao final.

## Impact

- Dependência nova: `anthropic` (Python SDK) — opcional, com fallback.
- Variável de ambiente: `ANTHROPIC_API_KEY` (lida do ambiente do processo).
- Custo operacional: ~1 chamada por job (≤ 5K tokens de entrada com a transcrição completa, 2K de saída JSON) → custo na casa de centavos.
- Latência adicional no estágio "seleção dos cortes": de ~50 ms (heurística) para ~3–6 s (chamada Claude). Cabe nos 3% atribuídos ao estágio na barra de progresso, sem reequilíbrio.
- `cuts.json` ganha campos novos; `report.md` final exibe título + rationale por corte.
- UI: nova seção de resultados com título do corte em negrito e rationale em itálico abaixo.
