## ADDED Requirements

### Requirement: Pipeline executa somente transcrição quando modo é "transcript"
O sistema SHALL aceitar `mode=transcript` no endpoint `/upload` e, nesse caso, executar apenas os estágios probe, transcribe e drive, retornando sem executar select, ass, outro, render, concat ou instagram.

#### Scenario: Upload com mode=transcript dispara apenas transcrição
- **WHEN** o usuário envia POST /upload com `mode=transcript`
- **THEN** o pipeline executa probe e transcribe
- **THEN** `transcript.txt` e `transcript.json` são gerados na pasta de output do job
- **THEN** nenhum arquivo de vídeo cortado é gerado

#### Scenario: Resultado do job em modo transcrição
- **WHEN** o pipeline de transcrição completa com sucesso
- **THEN** o evento SSE `type: "done"` contém `transcript_local_path` com o caminho local do `transcript.txt`
- **THEN** o evento contém `transcript_drive_url` com a URL do Drive (ou null se Drive não configurado)
- **THEN** o evento contém `cuts: []` (lista vazia)

#### Scenario: Upload para Drive em modo transcrição quando Drive está configurado
- **WHEN** o pipeline de transcrição completa e Drive está configurado
- **THEN** o sistema SHALL fazer upload do `transcript.txt` para o Google Drive
- **THEN** `transcript_drive_url` no resultado SHALL conter a URL pública do arquivo no Drive

#### Scenario: Modo padrão não é alterado
- **WHEN** o usuário envia POST /upload sem o campo `mode` (ou com `mode=cuts`)
- **THEN** o pipeline executa o fluxo completo atual (probe → transcribe → select → ass → outro → render → concat → instagram → drive)

### Requirement: Progresso SSE reflete os estágios do modo transcrição
O sistema SHALL emitir eventos SSE de progresso apenas para os estágios executados (probe, transcribe, drive) com pesos proporcionais para que a barra de progresso chegue a 100%.

#### Scenario: Eventos de progresso no modo transcrição
- **WHEN** o pipeline de transcrição está em execução
- **THEN** o sistema SHALL emitir evento `type: "stage"` para cada estágio executado (probe, transcribe, drive)
- **THEN** o `percent` acumulado SHALL chegar a 100.0 ao final do estágio drive
