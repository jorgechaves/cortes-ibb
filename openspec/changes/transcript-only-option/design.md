## Context

O Cortes IBB é uma aplicação FastAPI local com UI web onde o usuário arrasta um vídeo e dispara o pipeline completo: probe → transcribe → select → ass → outro → render → concat → instagram → drive. O resultado é enviado ao Google Drive e exibido na UI.

O único ponto de entrada de job é o endpoint `/upload`, que sempre executa o pipeline completo. Não há como interromper o processamento após a transcrição.

A transcrição já gera `transcript.txt` e `transcript.json` na pasta de output como parte do pipeline completo. O objetivo é expor esse resultado isoladamente, sem executar os demais estágios.

## Goals / Non-Goals

**Goals:**
- Permitir ao usuário escolher entre "Gerar Cortes" (modo atual) e "Só Transcrição" na UI
- Executar apenas probe + transcribe + drive no modo transcrição
- Reusar o stream SSE de progresso existente para o novo modo
- Enviar `transcript.txt` ao Drive se configurado, e exibir link de download na UI

**Non-Goals:**
- Alterar o pipeline de cortes existente
- Exportar transcrição em formato diferente de `.txt`
- Adicionar edição ou revisão do transcript na UI
- Suporte a múltiplos arquivos simultâneos

## Decisions

### 1. Parâmetro `mode` no endpoint `/upload` em vez de novo endpoint

O endpoint `/upload` já lida com upload, geração de job ID, controle de concorrência via `JobState` e disparo de thread. Duplicar toda essa lógica em `/upload-transcript` seria redundância desnecessária.

**Decisão:** adicionar `mode: str = Form("cuts")` ao `/upload`. Valores aceitos: `"cuts"` (padrão, comportamento atual) e `"transcript"`. A thread de execução chama `_run_pipeline` ou `_run_transcript_only` conforme o modo.

Alternativa descartada: novo endpoint `/upload-transcript` — código duplicado, complexidade de manutenção.

### 2. Nova função `pipeline.run_transcript_only()` em `pipeline/__init__.py`

O `pipeline.run()` atual tem stages entrelaçados com emissão de eventos globais ponderados por `STAGE_WEIGHTS`. Extrair o fluxo de transcrição como uma função separada mantém a legibilidade e evita flags condicionais espalhadas pelo `run()`.

**Decisão:** criar `run_transcript_only(source, out_dir, on_event)` que executa apenas probe + transcribe + drive e retorna um dict com `transcript_local_path` e `transcript_drive_url`. Os `STAGE_WEIGHTS` para o modo parcial serão: `upload: 5`, `probe: 10`, `transcribe: 75`, `drive: 10`.

### 3. Dois botões de ação na UI, com checkbox de legenda oculto em modo transcrição

A UI atual tem um botão "Gerar Cortes" e um checkbox de "Legenda". No modo "Só Transcrição" a legenda não é relevante.

**Decisão:** exibir dois botões lado a lado após o arquivo ser selecionado. O checkbox de legenda permanece visível apenas quando "Gerar Cortes" está ativo; fica oculto quando o usuário seleciona "Só Transcrição". O modo escolhido é enviado como campo `mode` no FormData do `/upload`.

### 4. Resultado da UI em modo transcrição

Quando o job concluir com `type: "done"` no SSE, a UI já exibe a tela de resultado com links de cortes. No modo transcrição, não há cortes — apenas o transcript.

**Decisão:** a UI detecta o modo pelo campo `mode` armazenado localmente (ou pelo campo `cuts` vazio no resultado) e exibe uma tela de resultado simplificada com: link de download local do `transcript.txt` e link do Drive (se disponível).

## Risks / Trade-offs

- **[Risco]** Usuário faz upload de vídeo muito longo só para transcrição e o processo trava → **Mitigação**: o timeout de 120s do Whisper já está configurado; o pipeline de transcrição lida com progresso incremental via SSE, então a UI continuará responsiva.
- **[Risco]** Drive não configurado: usuário não consegue acessar o arquivo remotamente → **Mitigação**: o link de download local (via `/files/{job_id}/transcript.txt`) sempre fica disponível na UI, independente do Drive.
- **[Trade-off]** Adicionar `mode` ao `/upload` em vez de endpoint dedicado: menos isolamento, mas evita duplicação de lógica de upload/concorrência. Aceitável dado o escopo da aplicação.
