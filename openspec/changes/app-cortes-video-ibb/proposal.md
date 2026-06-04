## Why

A change anterior (`cortes-video-ibb`) descreve um pipeline manual via skill `/video-use`. O operador real precisa de algo simples: rodar **um único comando**, abrir uma página no navegador, **arrastar o vídeo-fonte** e acompanhar tudo em uma **barra de progresso** até o upload concluir. Nada de terminal, nada de etapas separadas.

## What Changes

- Criar uma aplicação Python 3 single-file (`app.py`) que sobe um servidor HTTP local e abre automaticamente o navegador em `http://127.0.0.1:<porta>`.
- Servir uma UI HTML/JS estática (`index.html` embutido ou no diretório do app) com:
  - Drop zone para o vídeo (drag-and-drop + clique para selecionar).
  - Barra de progresso global (0–100%) com label do estágio atual.
  - Log/stream de eventos por linha (sucessos, avisos, erros).
- Backend Python expõe:
  - `POST /upload` (multipart) — recebe o vídeo e dispara o processamento em background.
  - `GET /events` (SSE) — stream de eventos `progress`/`stage`/`log`/`done`/`error` para a UI.
  - `GET /` — serve a UI.
- Orquestrar o pipeline da capability `video-cuts-ibb` (transcrição → seleção dos 6 cortes → render dos cortes com legendas + ícone + outro com logo → upload Drive) emitindo progresso por estágio.
- Empacotamento mínimo: rodar com `python3 app.py` (sem build step). Dependências instaladas via `requirements.txt`.
- Encerrar sozinho ao terminar (ou ficar de pé até `Ctrl+C`, configurável).

## Capabilities

### New Capabilities
- `video-cuts-app`: aplicação local Python3 + UI HTML com drag-and-drop e barra de progresso, que aciona o pipeline `video-cuts-ibb`.

### Modified Capabilities
- `video-cuts-ibb`: precisa expor o pipeline de forma **programática** (função/classe Python invocável com callback de progresso), em vez de ser executado apenas via skill manual. Isto altera o requisito de "como" o pipeline é acionado e introduz eventos de progresso.

## Impact

- Novos arquivos em `/Users/jorgehbchaves/Dev/teste2/`:
  - `app.py` (servidor + orquestração).
  - `web/index.html`, `web/app.js`, `web/styles.css` (UI).
  - `pipeline/` (módulos Python: transcrição, ASS, render, drive_upload) que encapsulam o pipeline atual.
  - `requirements.txt`.
- Dependências Python novas: `ffmpeg-python` (ou `subprocess`), `faster-whisper` (ou `openai-whisper` / `whisperx`), `google-api-python-client` + `google-auth-oauthlib` (para Drive, caso não use MCP); alternativamente, ler do MCP via integração externa — decisão final fica para o design.
- Sistema externo: `ffmpeg` ainda obrigatório no PATH.
- Skill `/video-use` deixa de ser dependência operacional — vira opcional/auxiliar para escolha humana dos trechos.
- Para a equipe IBB: o operador roda `python3 app.py`, abre `http://127.0.0.1:7860`, arrasta o MP4 e espera. Sem outras interações.
