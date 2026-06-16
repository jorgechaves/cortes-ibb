## Why

Atualmente, o pipeline sempre gera legendas ASS queimadas nos vídeos, mas nem todo vídeo precisa de legenda — por exemplo, pregações com slides ou entrevistas sem fundo musical. Permitir que o usuário escolha antes do upload evita retrabalho e torna o produto mais flexível.

## What Changes

- Ao arrastar (ou selecionar) um vídeo na dropzone, exibe um modal de confirmação perguntando se o vídeo terá legenda ou não
- A escolha é enviada ao backend junto com o upload (`subtitle=true|false`)
- O backend repassa o parâmetro ao pipeline
- O pipeline condiciona a geração de legendas ASS e a queima nas faixas de vídeo à flag recebida

## Capabilities

### New Capabilities

- `subtitle-prompt`: Modal de escolha de legenda exibido após o drag/drop, antes do upload iniciar. Captura a decisão do usuário (sim/não) e a envia ao backend.

### Modified Capabilities

- `upload-endpoint`: O endpoint `/upload` passa a aceitar o campo `subtitle` (boolean, form-data) e o repassa ao pipeline.
- `pipeline-render`: O pipeline condiciona as etapas `ass` e a queima de legenda no `render` à flag `with_subtitles`.

## Impact

- `web/index.html`: novo modal HTML + lógica JS para interceptar o drag/drop antes do upload
- `app.py`: endpoint `/upload` lê o campo `subtitle` do form-data
- `pipeline/__init__.py`: função `run()` recebe parâmetro `with_subtitles: bool`
- `pipeline/render.py`: `render_cut()` recebe `with_subtitles` e omite o filtro `ass` quando falso
