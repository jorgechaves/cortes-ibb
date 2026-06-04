## MODIFIED Requirements

### Requirement: Seleção dos 6 cortes
O sistema SHALL produzir exatamente 6 cortes a partir do vídeo-fonte fornecido pelo operador via UI. Cada corte SHALL ter duração-alvo de 60 segundos, com tolerância permitida entre 50 e 75 segundos quando necessário para preservar coerência. A seleção SHALL ser **totalmente automática em duas fases**:

1. **Fase candidata**: gerar 12–20 janelas-candidato de 50–75 s ancoradas em pausas >700 ms na transcrição, com preferência para fronteiras que ocorrem após pontuação final (`.`, `?`, `!`) e antes de uma palavra com inicial maiúscula que sinalize nova frase.
2. **Fase semântica**: submeter o texto de todos os candidatos em uma única chamada ao Claude API (`claude-haiku-4-5`) que retorna os **6 melhores** selecionados por: (a) ideia completa e auto-contida, (b) abertura clara, (c) fechamento conclusivo, (d) valor isolado quando assistido fora de contexto, (e) diversidade temática entre os 6 escolhidos.

Os 6 trechos finais SHALL ser numerados `corte-01` a `corte-06` na ordem cronológica em que aparecem no vídeo-fonte. Cada corte SHALL ter `slug`, `title` (até 8 palavras) e `rationale` (1 frase) atribuídos pelo modelo. Quando `ANTHROPIC_API_KEY` está ausente OU a chamada à API falha após 2 tentativas, o sistema SHALL cair em uma heurística estrita (pausa >700 ms + pontuação final no início e no fim do trecho) e SHALL marcar `selection_mode='heuristic'` no `cuts.json`, com aviso na UI.

#### Scenario: Seleção semântica bem-sucedida
- **WHEN** `ANTHROPIC_API_KEY` está configurada e a chamada ao Claude API retorna sucesso
- **THEN** os 6 cortes finais têm `selection_mode='semantic'`, com `title` e `rationale` preenchidos pelo modelo, em ordem cronológica no vídeo-fonte

#### Scenario: Coerência mínima por corte
- **WHEN** um corte é selecionado (semântico ou heurístico)
- **THEN** o trecho começa em uma fronteira de frase (após `.`/`?`/`!` ou após pausa >700 ms) e termina em uma fronteira de frase, dentro de 50–75 s

#### Scenario: Diversidade temática
- **WHEN** o Claude API retorna 6 escolhas e o vídeo tem duração maior que 8 minutos
- **THEN** os 6 trechos cobrem janelas que não se sobrepõem e estão distribuídos ao longo do vídeo, sem que dois trechos consecutivos comecem em uma diferença menor que 60s

#### Scenario: Fallback sem API key
- **WHEN** `ANTHROPIC_API_KEY` não está definida no ambiente
- **THEN** o pipeline emite um evento `log` com nível "warning" explicando o fallback, usa a heurística estrita para escolher 6 trechos, e os cortes ficam com `selection_mode='heuristic'`, `title` derivado das palavras-chave e `rationale` ausente

#### Scenario: Fallback após falha da API
- **WHEN** a chamada à Claude API falha duas vezes consecutivas (timeout, 5xx, erro de parsing do JSON retornado)
- **THEN** o pipeline emite `log` "warning" com o motivo, cai para a heurística estrita, e continua sem abortar o job

#### Scenario: Quantidade exata
- **WHEN** o pipeline termina a fase de seleção
- **THEN** existem exatamente 6 entradas em `cuts.json`, cada uma com `idx` único entre 1 e 6, `start`, `end`, `slug`, `title` e `selection_mode`
