## Why

O pipeline atual gera exatamente 6 cortes por vídeo, um número fixo hardcoded em toda a codebase. Palestras mais longas (40–90 min) têm material suficiente para 10 cortes de qualidade com arco narrativo completo, deixando conteúdo valioso inutilizado.

## What Changes

- O número de cortes gerados passa de **6 para 10**
- O seletor semântico passa a ranquear e selecionar 10 candidatos não-sobrepostos
- O seletor heurístico (fallback) passa a retornar até 10 cortes
- O gerador de legendas Instagram passa a aceitar e gerar posts para 10 cortes
- O schema JSON de validação do Instagram é atualizado de `minItems/maxItems: 6` para `10`
- O frontend exibe até 10 cards de resultado
- Pesos e distribuição de bins no gerador de candidatos são revisados para cobrir melhor vídeos com 10 regiões
- **A pasta criada no Google Drive passa a ter o mesmo nome da pasta de output** (ex: `20260611-104011-9259`) em vez de um nome genérico

## Capabilities

### New Capabilities

_(nenhuma nova capacidade conceitual — é expansão de capacidade existente)_

### Modified Capabilities

- `cut-selection`: número alvo de cortes muda de 6 para 10; seletor semântico aumenta buffer de ranqueamento (minItems 12→18, maxItems 18→24); seletor heurístico relaxa para 10 picks; distribuição de bins passa de 6 para 10
- `instagram-captions`: schema JSON atualizado para `minItems/maxItems: 10`; prompt ajustado para solicitar 10 posts

## Impact

- `pipeline/selector.py`: constante implícita 6 → 10 em `gather_candidates` (bins), `pick_six_heuristic`
- `pipeline/semantic_selector.py`: schema `minItems/maxItems`, prompt, `_greedy_nonoverlap` target
- `pipeline/instagram.py`: schema `minItems/maxItems`, `_validate`, `generate`
- `pipeline/__init__.py`: comentários e guards que assumem 6 cortes
- `pipeline/drive.py`: lógica de criação/busca de pasta no Drive passa a usar o `job_id` (nome da pasta de output) como nome da pasta no Drive
- `web/index.html`: badge "6 cortes" → dinâmico (já é dinâmico via JS — sem mudança necessária)
