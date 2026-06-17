## Why

O pipeline atual sempre executa o fluxo completo (transcrição → seleção de cortes → renderização → upload), mas às vezes o usuário só precisa do transcript.txt do vídeo original para revisar o conteúdo, sem precisar gerar nenhum corte. Não há como pedir apenas a transcrição sem disparar todo o processo.

## What Changes

- Adicionar uma segunda opção na UI após arrastar o vídeo: "Só Transcrição" (além do botão já existente de gerar cortes)
- Adicionar endpoint `/upload-transcript` no backend (ou reusar `/upload` com novo parâmetro `mode=transcript`) que executa apenas probe + transcribe e retorna o transcript.txt
- O pipeline precisa de um modo de execução parcial que pare após a etapa de transcrição
- Resultado exibido na UI: link para download do transcript.txt e (se Drive configurado) link do Google Drive

## Capabilities

### New Capabilities

- `transcript-only-mode`: Modo de execução do pipeline que executa somente probe + transcribe, gera transcript.txt e transcript.json, faz upload para o Drive se configurado, e retorna o resultado sem realizar cortes, renderização ou geração de conteúdo Instagram.

### Modified Capabilities

- `video-upload-ui`: A tela de upload precisa exibir dois botões de ação após o vídeo ser selecionado/arrastado: "Gerar Cortes" (fluxo atual) e "Só Transcrição" (novo modo).

## Impact

- `app.py`: novo endpoint ou parâmetro de modo no `/upload`; nova função `_run_transcript_only`
- `pipeline/__init__.py`: nova função `run_transcript_only()` que executa apenas probe + transcribe + drive
- `web/index.html`: UI de upload ganha segundo botão de ação; lógica de exibição de resultado mostra link do transcript no modo transcrição
