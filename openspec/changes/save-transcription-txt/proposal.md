## Why

Atualmente a transcrição é salva apenas como `transcript.json` (palavra por palavra com timestamps), inacessível para leitura humana. Um arquivo `transcript.txt` com o texto corrido completo facilita revisão, busca, e uso externo da transcrição sem depender de ferramentas técnicas.

## What Changes

- Após a transcrição, salvar `transcript.txt` na pasta do job com o texto completo das palavras unidas, com quebras de linha em pausas longas (> 1,5 s) para melhorar a legibilidade
- Incluir `transcript.txt` na lista de arquivos enviados ao Google Drive
- Expor o caminho/link do arquivo no resultado final do job

## Capabilities

### New Capabilities

- `transcription-txt-export`: Geração e salvamento de `transcript.txt` com o texto corrido da transcrição completa do vídeo original, incluindo upload ao Drive e presença no resultado.

### Modified Capabilities

_(nenhuma)_

## Impact

- `pipeline/transcribe.py`: função `transcribe()` passa a salvar `transcript.txt` além de `transcript.json`
- `pipeline/__init__.py`: adiciona `transcript.txt` à lista de upload ao Drive; inclui `transcript_path` no resultado
- `web/index.html`: exibe link para o `transcript.txt` no Drive (se disponível) na seção de resultados
