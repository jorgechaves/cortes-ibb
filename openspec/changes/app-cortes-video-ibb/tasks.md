## 1. Layout do projeto e dependências

- [x] 1.1 Criar `requirements.txt` com: `fastapi`, `uvicorn[standard]`, `python-multipart`, `faster-whisper`, `google-api-python-client`, `google-auth-httplib2`, `google-auth-oauthlib`
- [x] 1.2 Criar estrutura de pastas: `web/`, `pipeline/`, `output/`
- [x] 1.3 Adicionar `.gitignore` cobrindo `output/`, `__pycache__/`, `*.token.json`, modelos do Whisper
- [x] 1.4 Documentar instalação em `README.md` (instalar ffmpeg + `pip install -r requirements.txt` + `python3 app.py`)

## 2. Módulos do pipeline (puro Python, callback `on_event`)

- [x] 2.1 `pipeline/__init__.py` expondo `run(source, icon, logo, out_dir, on_event)` — orquestra todos os estágios
- [x] 2.2 `pipeline/probe.py` — `ffprobe` → retorna `{width,height,fps,duration,vcodec,acodec}`
- [x] 2.3 `pipeline/transcribe.py` — faster-whisper (`small`, language=`pt`, word_timestamps=True); grava `transcript.json`; emite `progress` por chunk
- [x] 2.4 `pipeline/selector.py` — heurística de 6 trechos baseados em pausas >500 ms; retorna `[{idx, start, end, slug}]`
- [x] 2.5 `pipeline/ass_builder.py` — para cada trecho, gera `.ass` com Antique Olive 14pt, branco, Outline=1, Alignment=2, MarginV=90, chunking 2 palavras MAIÚSCULO
- [x] 2.6 `pipeline/outro.py` — gera `outro.mp4` (2s, logo.png centralizada em fundo branco, mesmo W×H/fps do source, áudio AAC silencioso)
- [x] 2.7 `pipeline/render.py` — para cada corte: `ffmpeg -ss/-to` + filtro `subtitles + overlay(icone)`, parse `out_time_ms` para progresso por corte
- [x] 2.8 `pipeline/concat.py` — concat demuxer (corte + outro) com fallback de reencode quando timebase difere
- [x] 2.9 `pipeline/drive.py` — fluxo OAuth Desktop (`InstalledAppFlow`), localizar pasta `videos-ibb`, upload resumable com callback de progresso, persistir `token.json` em `~/.config/cortes-ibb/`
- [x] 2.10 Testes manuais de cada módulo isoladamente com um vídeo curto de exemplo

## 3. Servidor FastAPI (`app.py`)

- [x] 3.1 Inicialização: escolher porta livre 7860–7870, montar `web/` como estáticos, abrir navegador com `webbrowser.open`
- [x] 3.2 Verificações de pré-flight: `ffmpeg --version`, `ffprobe -version`; abortar com instrução clara se ausentes
- [x] 3.3 Estado global thread-safe: `current_job = {id, status, percent, queue: queue.Queue}`
- [x] 3.4 `GET /` — servir `web/index.html`
- [x] 3.5 `POST /upload` (multipart) — salvar em `output/<job-id>/source.mp4`, criar Thread chamando `pipeline.run` com callback que faz `queue.put(event)`
- [x] 3.6 `GET /events` — `StreamingResponse(media_type='text/event-stream')`, lê da `Queue` e emite `data: <json>\n\n`; encerra após evento `done` ou `error`
- [x] 3.7 `POST /shutdown` — responde 200, agenda `os._exit(0)` em background timer (200 ms)
- [x] 3.8 Tratar concorrência: se já existe job ativo, `POST /upload` responde 409 `{"error":"job in progress"}`
- [x] 3.9 Cálculo do progresso global a partir dos eventos do pipeline (pesos do design)

## 4. UI (`web/index.html`)

- [x] 4.1 Layout: header com título "Cortes IBB", drop zone grande, barra de progresso, label de estágio, log scrollable, área de resultados
- [x] 4.2 Drop zone: aceita drag-and-drop e clique para abrir file picker; valida `type.startsWith('video/')`
- [x] 4.3 Upload via `fetch('/upload', { method: 'POST', body: FormData })`; trocar UI para estado "Processando"
- [x] 4.4 `EventSource('/events?jobId=...')` — atualiza barra `<progress>` e label do estágio; append no log; reconectar em caso de erro de stream
- [x] 4.5 Estado de erro: banner vermelho com mensagem + botão "Tentar novamente" (reseta a UI sem refresh)
- [x] 4.6 Estado `done`: ocultar barra, mostrar lista de 6 cortes com nome, duração e link Drive (`https://drive.google.com/file/d/<id>/view`)
- [x] 4.7 Botão "Encerrar app" chama `POST /shutdown`

## 5. Cálculo de progresso e parsing do ffmpeg

- [x] 5.1 Definir pesos por estágio (constante compartilhada entre `app.py` e `pipeline/__init__.py`)
- [x] 5.2 Em `render.py`, rodar `ffmpeg -progress pipe:1` e parsear `out_time_ms` vs duração do trecho → emitir `progress` com `percent` por corte
- [x] 5.3 Em `drive.py`, usar `MediaFileUpload(resumable=True)` com chunk callback → emitir `progress` por upload
- [x] 5.4 Em `transcribe.py`, emitir `progress` por segmento processado (faster-whisper expõe `info.duration` e iteração por segmento)

## 6. Setup automático na 1ª execução

- [x] 6.1 Verificar fonte Antique Olive (`fc-list | grep -i 'antique olive'`); se ausente, emitir aviso na UI (banner amarelo) e usar fallback `Arial Black`
- [x] 6.2 Criar `~/.config/cortes-ibb/` se ausente; instruções na UI quando `credentials.json` está faltando
- [x] 6.3 Fluxo OAuth na 1ª autenticação: rodar `InstalledAppFlow.run_local_server(port=0)` e salvar `token.json`
- [x] 6.4 Cache do modelo Whisper: respeitar `HF_HOME`/`XDG_CACHE_HOME` padrão; emitir log "Baixando modelo..." na primeira vez

## 7. Validação end-to-end

- [ ] 7.1 Rodar `python3 app.py` com o vídeo real (`EB5B4AAD-2E7B-412E-9A3B-10B0F49D8A19.MP4`)
- [ ] 7.2 Confirmar que abre o navegador automaticamente
- [ ] 7.3 Arrastar o vídeo, acompanhar barra de progresso do 0 ao 100%
- [ ] 7.4 Conferir 6 arquivos em `output/<job-id>/` com nomes `corte-XX-<slug>.mp4`
- [ ] 7.5 Conferir pasta `videos-ibb` no Drive com os 6 arquivos
- [ ] 7.6 Testar caminhos de erro: ffmpeg ausente, token expirado, drop de arquivo não-vídeo, segundo drop durante job ativo
- [ ] 7.7 Gerar `output/<job-id>/report.md` com resumo (cortes, slugs, IDs Drive, durações)

## 8. Encerramento

- [x] 8.1 Documentar limitações conhecidas no README (1 job por vez, só Mac, modelo Whisper baixa na 1ª vez)
- [ ] 8.2 Marcar a change como pronta para `/opsx:archive` quando o teste end-to-end estiver verde
