## MODIFIED Requirements

### Requirement: Barra de progresso por estágio
A UI SHALL exibir uma barra de progresso global (0–100%) que reflete o avanço ponderado dos estágios: `upload (5%)`, `probe (2%)`, `transcrição (25%)`, `seleção dos cortes (3%)`, `legendas ASS (5%)`, `cartão final (5%)`, `render dos 6 cortes (35%)`, `concat (5%)`, `instagram (5%)`, `upload Drive (10%)`. A UI SHALL mostrar o rótulo do estágio atual e um sub-progresso quando aplicável (ex.: "Renderizando corte 3 de 6 — 47%").

#### Scenario: Estágio Instagram visível
- **WHEN** o backend está no estágio `instagram`
- **THEN** a barra mostra ~80% e o rótulo "Gerando legendas Instagram"

#### Scenario: Conclusão
- **WHEN** todos os estágios terminam com sucesso (inclusive upload no Drive)
- **THEN** a barra mostra 100%, o rótulo muda para "Concluído" e a UI lista os 6 arquivos com IDs do Drive e as 6 legendas de Instagram

### Requirement: Resultado final visível na UI
Ao terminar com sucesso, a UI SHALL exibir uma lista dos 6 cortes contendo, para cada um: índice (1–6), `title` em negrito, `rationale` em itálico, nome do arquivo local, duração, link Drive, botão **Abrir pasta local** e — quando disponíveis — as legendas de Instagram (hook, caption, CTA, hashtags) com botão **Copiar** que coloca no clipboard o texto formatado para colar no Instagram. Quando `selection_mode='heuristic'`, a UI SHALL renderizar aviso amarelo no topo. Quando `instagram_skipped=true`, a UI SHALL renderizar aviso amarelo separado explicando o motivo. A UI SHALL persistir esse resultado até o operador soltar um novo vídeo.

#### Scenario: Resultado completo
- **WHEN** o pipeline finaliza com `selection_mode='semantic'` e legendas Instagram geradas
- **THEN** cada uma das 6 linhas exibe: índice, título, rationale, arquivo + duração, link Drive, e abaixo a seção de Instagram (hook, caption, CTA, hashtags) com botão Copiar funcional

#### Scenario: Resultado sem legendas Instagram
- **WHEN** `instagram_skipped=true`
- **THEN** a UI exibe banner amarelo "Legendas Instagram não geradas — <motivo>" e as linhas dos cortes não mostram a seção de legenda nem o botão Copiar
