## Context

A change anterior (`cortes-video-ibb`) define o quê: 6 cortes editados + upload no Drive. Esta change define o como operacional: uma app local com servidor HTTP Python e UI HTML para drag-and-drop, com barra de progresso unificada.

Stakeholders:
- Operador IBB: roda `python3 app.py` no Mac, arrasta o vídeo e espera.
- Equipe técnica: mantém o pipeline e dependências; precisa de instalação simples (`pip install -r requirements.txt`).

Restrições/cenário inicial:
- Mac (Darwin 24.6.0), Python 3 disponível (presume-se 3.10+).
- `ffmpeg`/`ffprobe` precisam estar no PATH (pré-condição já existente).
- Sem usuário admin: instalação só com `pip install --user` ou venv local.
- Decisões do operador já tomadas: OAuth local para Drive, seleção 100% automática, transcrição com `faster-whisper`.

## Goals / Non-Goals

**Goals:**
- 1 comando para subir o app, 1 ação no navegador (arrastar o vídeo).
- Feedback visual contínuo: barra de progresso global + estágio textual + log scroll.
- Zero prompts terminal ou modais bloqueantes durante o processamento.
- Pipeline programático, testável fora da UI (módulo Python importável).
- Robustez mínima: erros em qualquer estágio são reportados na UI sem derrubar o servidor.

**Non-Goals:**
- Não vamos empacotar como `.app` / `.dmg` / `pyinstaller`. Roda como script.
- Não vamos suportar processamento concorrente (1 job por vez).
- Não vamos persistir histórico de jobs entre execuções.
- Não vamos hospedar remotamente — só `127.0.0.1`.
- Não vamos suportar Windows/Linux nesta primeira versão (foco no Mac do operador).

## Decisions

### Decisão 1: Stack web — stdlib + FastAPI/uvicorn
Optar por **FastAPI + uvicorn** (em vez de Flask ou `http.server` puro):
- SSE é trivial (`StreamingResponse` com `text/event-stream`).
- Upload `multipart/form-data` nativo via `UploadFile`.
- Tipagem forte ajuda na manutenção do pipeline.
- Dependência leve (`fastapi`, `uvicorn[standard]`, `python-multipart`).

**Alternativa considerada:** `http.server` puro. Rejeitado porque SSE + multipart exigem código manual que vira fonte de bugs.

### Decisão 2: Frontend — HTML estático single-file
`web/index.html` com `<style>` e `<script>` inline (ou módulos simples em `web/`). Sem framework — vanilla JS é suficiente para drop zone, fetch upload e EventSource. Empacotar tudo num único `index.html` facilita servir e debugar.

Componentes da UI:
- Drop zone (`<div>` com listeners `dragover`/`drop`).
- Barra de progresso (`<progress>` + label `<span>` para estágio).
- Log scroll (`<ul>` append-only, scroll automático).
- Lista de resultados (renderizada após `done`).

### Decisão 3: Modelo de jobs — 1 ativo, em thread de background
Para manter o app simples: um único job por vez. O endpoint `/upload` cria o job e dispara uma `threading.Thread` (não asyncio, porque `ffmpeg`/`faster-whisper` são CPU/IO sync e bloqueariam o loop). Uma `queue.Queue` thread-safe é a ponte com o gerador SSE que serve `/events`.

Estado global no app: `current_job = {id, status, last_percent, queue}`. Tentativas de novo upload com job ativo respondem 409 Conflict.

**Alternativa considerada:** asyncio + run_in_executor. Rejeitado: adiciona complexidade sem benefício (1 job por vez).

### Decisão 4: Cálculo da barra de progresso
Pesos por estágio definidos no spec (`upload 5%`, `probe 2%`, `transcrição 25%`, `seleção 3%`, `legendas 5%`, `outro 5%`, `render 40%`, `concat 5%`, `upload Drive 10%`). O pipeline emite progresso normalizado dentro de cada estágio (0.0–1.0); o app converte para porcentagem global usando offset + peso. Para o estágio de render (40% de 6 cortes), cada corte vale ~6.67% e seu sub-progresso é lido do stderr do `ffmpeg` (parsing de `out_time_ms` e `total_duration`).

### Decisão 5: Estrutura do código
```
/
├── app.py                  # FastAPI app + SSE + estado de job
├── requirements.txt
├── web/
│   └── index.html          # UI single-file
└── pipeline/
    ├── __init__.py         # def run(source, icon, logo, out_dir, on_event)
    ├── probe.py            # ffprobe wrapper
    ├── transcribe.py       # faster-whisper wrapper, retorna words[]
    ├── selector.py         # algoritmo dos 6 trechos
    ├── ass_builder.py      # gera os arquivos .ass
    ├── outro.py            # gera outro.mp4 com logo
    ├── render.py           # render dos cortes (ffmpeg)
    ├── concat.py           # concat cortes + outro
    └── drive.py            # OAuth + upload Google Drive
```

`app.py` importa apenas `pipeline.run`. Tudo do pipeline é puro Python, testável standalone.

### Decisão 6: Transcrição com faster-whisper
- Modelo padrão: `small` (1GB RAM, rápido) em português (`language="pt"`).
- Configurável via env: `WHISPER_MODEL=medium` para qualidade maior.
- Word-level timestamps habilitados (`word_timestamps=True`).
- Output gravado em `output/<job-id>/transcript.json` para debug.

### Decisão 7: Seleção automática dos 6 trechos
Algoritmo:
1. Construir lista de "pontos de pausa" — gaps entre palavras consecutivas com gap > 0.5s.
2. Tentar 6 janelas de ~60s não-sobrepostas que comecem/terminem em pausas.
3. Distribuir as 6 janelas pela duração total (uniforme, com pequenas variações para casar em pausas).
4. Para cada janela escolhida, derivar `slug` das 2–4 palavras mais frequentes não-stopwords do trecho.

Se a heurística falhar (vídeo muito curto, sem pausas suficientes), o pipeline emite `error` com mensagem clara.

### Decisão 8: Google Drive — OAuth Desktop
Fluxo:
1. App procura `~/.config/cortes-ibb/credentials.json` (client OAuth tipo "Desktop app", criado uma vez pelo operador no Google Cloud Console).
2. Se ausente, abre a UI em uma página de instrução com link "Como criar credenciais" e impede uploads.
3. Primeira execução: `InstalledAppFlow.run_local_server(port=0)` → abre navegador para consent → salva `token.json`.
4. Próximas execuções: carrega `token.json`, faz refresh transparente.
5. Upload com `MediaFileUpload(..., resumable=True)` para arquivos grandes; chunk callback alimenta o progresso (10% global dividido por 6).

Scope: `https://www.googleapis.com/auth/drive.file` (acessa só arquivos criados pelo app, mínimo necessário).

### Decisão 9: Encerramento
Botão "Encerrar" na UI faz `POST /shutdown`, que chama `os._exit(0)` após responder. Sem isso, `Ctrl+C` no terminal. Não fechar automaticamente após terminar — operador pode arrastar outro vídeo na sequência.

## Risks / Trade-offs

- **faster-whisper exige download inicial do modelo (~500MB–1.5GB)** → primeira execução demora muito. Mitigação: barra mostra "Baixando modelo Whisper..." e cache reaproveita.
- **OAuth desktop precisa de `credentials.json` do operador** → fricção na 1ª config. Mitigação: instruções claras na UI quando o arquivo está ausente; só roda 1 vez.
- **Vídeos de 200 MB+ pelo upload HTTP local** → demora alguns segundos copiando para `output/`. Mitigação: barra de upload já reflete isso (5% do total).
- **Render de 6 cortes em série pode levar 5–15 min em CPU** → operador precisa esperar. Mitigação: barra de progresso por corte mantém o operador informado; encurtar com `-preset fast` se for aceitável.
- **Antique Olive ausente** → fallback para `Arial Black` muda o visual. Mitigação: aviso explícito na UI no início do job, log mostra a fonte usada.
- **Thread única do FastAPI fica bloqueada por requests sync grandes** → uvicorn padrão é async; chamar `def` sync (não `async def`) move o handler para threadpool. Verificar que o upload usa endpoint `def` (sync) ou `async def` com `await file.read()` em chunks.
- **Operador roda dois `python3 app.py`** → conflito de porta resolvido pela escolha 7860–7870; pasta `output/` compartilhada, mas job-id único evita colisão.

## Migration Plan

Não há migração de sistemas. Para o operador que já estava planejando rodar a skill manualmente: passa a usar o app — basta `pip install -r requirements.txt` e `python3 app.py`.

A change `cortes-video-ibb` continua válida como descrição do pipeline; esta change adiciona a camada de aplicação e modifica o requisito de "como" o pipeline é acionado.

## Open Questions

- Qual `client_id`/`client_secret` do Google Cloud usar? Resolução: documentar instruções de criação na 1ª execução; usuário cria seu próprio projeto OAuth (não distribuímos chaves).
- Whisper `small` vs `medium`: qual o ponto bom para o vídeo da IBB (provavelmente português falado claramente)? Resolução: `small` por padrão; trocar via `WHISPER_MODEL` env var se a qualidade pedir.
- Resultado final: além de listar IDs do Drive, gerar um relatório `output/<job-id>/report.md`? Sugestão sim, gerado sempre — útil para auditoria.
