## Context

O app Cortes IBB recebe um vídeo via drag-and-drop ou file picker no `web/index.html`, faz upload para o endpoint `POST /upload` em `app.py`, e executa o pipeline completo em `pipeline/__init__.py`. O pipeline sempre passa pela etapa `ass` (gera legendas ASS para cada corte) e depois chama `render_cut` em `pipeline/render.py` que queima a legenda no vídeo usando o filtro `subtitles=` do FFmpeg. Não existe hoje nenhum mecanismo para pular esta etapa.

## Goals / Non-Goals

**Goals:**
- Exibir um modal de escolha antes do upload com duas opções: "Sim, com legenda" e "Não, sem legenda"
- Transmitir a escolha ao backend como campo form-data `subtitle` (`true`/`false`)
- No pipeline, quando `with_subtitles=False`, pular a geração de arquivos ASS e não aplicar o filtro `subtitles=` no FFmpeg

**Non-Goals:**
- Alterar a lógica de seleção de cortes ou transcrição (Whisper roda sempre)
- Permitir legenda opcional por corte (a flag é global para o job)
- Persistir a preferência do usuário entre sessões

## Decisions

### 1. Modal no frontend antes do upload (não após)
Interceptar o drag/drop e click do file picker para mostrar o modal **antes** de chamar `startUpload()`. Alternativa considerada: mostrar um toggle no header da página — descartada porque exige o usuário lembrar de configurar antes de arrastar.

### 2. Flag como campo `subtitle` no form-data multipart
O upload já usa `FormData` com `video`. Adicionar `subtitle: "true"/"false"` é a adição mais simples e compat com `UploadFile = File(...)` + `Form(...)` no FastAPI. Alternativa: query param — descartada porque mistura semântica de parâmetros.

### 3. Assinatura `run(..., with_subtitles: bool = True)`
Parâmetro com default `True` garante retrocompatibilidade com qualquer chamada direta ao pipeline fora do servidor. Quando `False`, as etapas `ass` e o filtro `subtitles=` são pulados; o `render_cut` usa filtro simplificado com apenas o overlay do ícone.

### 4. `render_cut` recebe `ass_path` como `str | None`
Quando `with_subtitles=False`, `ass_path=None` é passado e o filter_complex usa apenas `[0:v]` com scale+overlay do ícone, sem a parte `subtitles=`. Isso mantém a assinatura coerente sem introduzir um segundo code path completamente separado.

## Risks / Trade-offs

- [Usuário esquece de escolher] → O modal bloqueia o upload; não há upload sem uma escolha explícita.
- [Modal quebrando o fluxo em dispositivos touch] → O modal é HTML/CSS simples sem dependências externas, compatível com todos os browsers modernos.
- [Stages weights incorretos quando `ass` é pulado] → `STAGE_WEIGHTS` continua com peso para `ass`, mas a etapa simplesmente emite progresso instantâneo quando pulada; o impacto na barra global é mínimo (5%).

## Migration Plan

Nenhuma migração de dados necessária. A flag é por-job e volátil. Deploy é substituição direta dos arquivos `app.py`, `pipeline/__init__.py`, `pipeline/render.py` e `web/index.html`.
