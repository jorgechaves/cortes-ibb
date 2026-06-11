## ADDED Requirements

### Requirement: Pipeline generates ten cuts
O pipeline SHALL selecionar e renderizar exatamente 10 cortes por run (salvo fallback documentado abaixo).

#### Scenario: Run completo com vídeo longo
- **WHEN** o vídeo tem duração suficiente (≥ 15 min) e candidatos disponíveis ≥ 10
- **THEN** o pipeline entrega exatamente 10 arquivos MP4 e 10 entradas em `cuts.json`

#### Scenario: Vídeo curto sem candidatos suficientes
- **WHEN** `gather_candidates` retorna menos de 10 candidatos mesmo com fallback de 45s
- **THEN** o pipeline entrega o máximo disponível (< 10) sem falhar, e loga aviso explicando o motivo

### Requirement: Candidate generator usa 10 bins de distribuição
O gerador de candidatos SHALL distribuir os candidatos em 10 bins temporais ao longo do vídeo, com até `ceil(50/10) = 5` candidatos por bin.

#### Scenario: Vídeo com cobertura temporal uniforme
- **WHEN** o vídeo tem pausas distribuídas ao longo de toda a duração
- **THEN** os 50 candidatos (cap) cobrem os 10 segmentos temporais proporcionalmente

### Requirement: Seletor semântico ranqueia e seleciona 10 cortes não-sobrepostos
O seletor semântico SHALL solicitar ao LLM um ranking de 18–24 candidatos e aplicar `_greedy_nonoverlap` com target = 10.

#### Scenario: LLM retorna ranking com candidatos sobrepostos
- **WHEN** o LLM ranqueia candidatos e alguns se sobrepõem temporalmente
- **THEN** o greedy seleciona os 10 melhores não-sobrepostos em ordem de ranking

#### Scenario: Ranking insuficiente para 10 não-sobrepostos na primeira tentativa
- **WHEN** o greedy encontra menos de 10 não-sobrepostos no ranking retornado
- **THEN** o sistema tenta novamente (temperature 0.0) e loga o motivo

### Requirement: Seletor heurístico retorna até 10 cortes
O seletor heurístico (fallback) SHALL selecionar greedy não-sobreponível com target = 10.

#### Scenario: Fallback ativado por falha semântica
- **WHEN** o seletor semântico falha (API indisponível ou sem chave)
- **THEN** `pick_n_heuristic(n=10)` retorna até 10 cortes não-sobrepostos em ordem cronológica

### Requirement: Fallback de duração mínima para 10 cortes
O pipeline SHALL tentar primeiro com `target_min=60s`; se obtiver menos de 10 candidatos, reattempt com `target_min=45s`.

#### Scenario: Vídeo médio com poucos candidatos de 60s
- **WHEN** `gather_candidates(target_min=60)` retorna menos de 10 candidatos
- **THEN** o pipeline reloga e chama `gather_candidates(target_min=45)` automaticamente
