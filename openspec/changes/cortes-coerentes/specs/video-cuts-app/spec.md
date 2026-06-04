## MODIFIED Requirements

### Requirement: Resultado final visível na UI
Ao terminar com sucesso, a UI SHALL exibir uma lista dos 6 cortes contendo, para cada um: índice (1–6), `title` curto em negrito, `rationale` em itálico abaixo (se disponível), nome do arquivo local, duração, link clicável para o arquivo no Drive e botão "Abrir pasta local" que aponta para `output/<job-id>/`. Quando `selection_mode='heuristic'`, a UI SHALL renderizar um aviso amarelo no topo da lista informando que a seleção semântica não foi usada (com motivo). A UI SHALL persistir esse resultado até o operador soltar um novo vídeo na drop zone.

#### Scenario: Resultado com seleção semântica
- **WHEN** o pipeline finaliza com `selection_mode='semantic'` para todos os cortes
- **THEN** a UI renderiza 6 linhas com `title` em negrito, `rationale` em itálico, nome do arquivo, duração, link Drive e botão "Abrir pasta local", sem banner de aviso

#### Scenario: Resultado com fallback heurístico
- **WHEN** o pipeline finaliza com `selection_mode='heuristic'` para os cortes
- **THEN** a UI exibe um banner amarelo no topo: "Seleção semântica indisponível — usando heurística (motivo: <razão>)" e as 6 linhas sem o campo `rationale`
