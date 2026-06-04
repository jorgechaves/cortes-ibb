## Context

O vídeo-fonte `EB5B4AAD-2E7B-412E-9A3B-10B0F49D8A19.MP4` (~200 MB) está em `/Users/jorgehbchaves/Dev/teste2/`, ao lado de `icone.png` e `logo.png`. A tarefa será executada localmente com `ffmpeg` (presumindo libass + libfreetype) e a skill `/video-use` para escolha de cortes e geração da transcrição. O upload final usa o MCP `claude.ai Google Drive` já configurado.

Stakeholders: equipe de comunicação da IBB (consumidora dos cortes), operador local que executará o `/opsx:apply` (responsável por rodar a skill e validar visualmente cada corte antes do upload).

Restrições principais:
- Fonte Antique Olive precisa estar instalada (ou substituída por equivalente declarada antes da execução).
- O MCP Drive expõe operações por arquivo (`create_file`) — não há sincronização de pasta nativa; o upload precisa enviar arquivo por arquivo após localizar a pasta `videos-ibb`.
- O vídeo-fonte tem ~200 MB; codificar 6 cortes + cartão final exigirá espaço de scratch local na ordem de 1–2 GB.

## Goals / Non-Goals

**Goals:**
- Pipeline determinístico e repetível: a partir do vídeo-fonte + assets, gerar 6 MP4 prontos para publicação.
- Estilo visual consistente entre cortes (legendas, ícone, cartão final).
- Upload automatizado para a pasta correta do Drive com nomes preservados.
- Trabalho artesanal nos pontos onde o juízo humano agrega valor: seleção dos trechos e revisão pós-edição.

**Non-Goals:**
- Não publicar diretamente em redes sociais; somente entregar no Drive.
- Não traduzir áudio nem criar legendas em idioma diferente do original.
- Não reescalonar/normalizar áudio musicalmente; apenas reencodar para AAC.
- Não converter o vídeo para vertical/redimensionar — manter resolução do original.

## Decisions

### Decisão 1: Skill `/video-use` orquestra a edição
Usaremos `/video-use` para: (a) transcrição com timestamps, (b) sugestão e marcação dos 6 trechos, (c) montagem dos filtros `ffmpeg`. A skill já encapsula as boas práticas de chunking de legenda (2 palavras) e composições com `overlay` + `subtitles`.

**Alternativa considerada:** script puro em Python (whisperx + moviepy). Rejeitado porque (1) duplica trabalho que a skill já faz e (2) o usuário pediu explicitamente para usar `/video-use`.

### Decisão 2: Legendas como ASS, queimadas via `subtitles` filter
Cada corte produz um arquivo `corte-XX.ass` com estilo:
```
Style: Default,Antique Olive,14,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,
       0,0,0,0,100,100,0,0,1,1,0,2,10,10,90,1
```
- `PrimaryColour=&H00FFFFFF` (branco), `OutlineColour=&H00000000` (preto), `Outline=1`, `Shadow=0`.
- `Alignment=2`, `MarginV=90`, fonte `Antique Olive` 14pt.
- Chunking: máximo 2 palavras por linha (`max_chars` virtualmente ignorado em favor do limite por palavras); todas as linhas convertidas para `.upper()`.

Quem aplica: `ffmpeg -vf "subtitles=corte-XX.ass:fontsdir=/Library/Fonts"` (ajustar `fontsdir` ao SO).

**Alternativa considerada:** SRT + force_style. Rejeitado porque o controle fino de chunking (2 palavras) e MarginV=90 fica frágil em SRT.

### Decisão 3: Ícone via `overlay`, com guardas de margem
O ícone será escalado por altura para algo entre 80 e 96 px (resolução padrão 1080p → altura 88 px). Composição:
```
[0:v]subtitles=corte-XX.ass[v0];
[1:v]scale=-1:88[ic];
[v0][ic]overlay=x=36:y=36:enable='lte(t,DUR_CONTEUDO)'[vfinal]
```
- `x=36, y=36` garante mais que os 24 px exigidos (sem encostar nas bordas).
- `enable='lte(t,...)'` faz o ícone desaparecer no cartão final.

### Decisão 4: Cartão final concatenado, não overlay temporizado
Gera-se um clipe estático `outro-XX.mp4` com `logo.png` em fundo branco do mesmo tamanho e fps do corte:
```
ffmpeg -y -loop 1 -t 2 -i logo.png \
  -f lavfi -t 2 -i anullsrc=channel_layout=stereo:sample_rate=48000 \
  -vf "scale=W:H:force_original_aspect_ratio=decrease,pad=W:H:(ow-iw)/2:(oh-ih)/2:white,format=yuv420p,fps=FPS" \
  -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest outro-XX.mp4
```
O corte final é a concatenação (`concat demuxer`) do corte editado com o `outro-XX.mp4`. Isso evita conflitos com legendas/ícone temporizados e mantém o áudio claramente silenciado nos 2s finais.

**Alternativa considerada:** overlay com `enable='gte(t,...)'`. Rejeitado: ainda passa áudio do corte por baixo (a menos que se silencie com filtros) e complica o framing.

### Decisão 5: Codificação H.264/AAC com CRF 20
`-c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p -c:a aac -b:a 160k -movflags +faststart`.
- CRF 20 dá qualidade próxima do original sem inflar o tamanho.
- `+faststart` ajuda o streaming no Drive.
- Resolução e fps preservados (probe inicial com `ffprobe`).

### Decisão 6: Upload via MCP Drive em duas etapas
1. `search_files` por `name='videos-ibb'` e `mimeType='application/vnd.google-apps.folder'` para obter o ID.
2. Para cada corte: `create_file` com `parents=[folderId]`, `name='corte-XX-<slug>.mp4'`, `mimeType='video/mp4'`, conteúdo a partir do arquivo local.

Se a pasta não existir, o operador é avisado e o pipeline pausa antes de criar uma nova (evita pasta duplicada).

## Risks / Trade-offs

- **Fonte Antique Olive ausente** → ffmpeg substitui silenciosamente por uma fonte padrão. Mitigação: validar a fonte com `fc-list | grep -i 'antique olive'` antes de renderizar; se ausente, alertar e parar.
- **Whisper marca timestamps grosseiros** → palavras saem fora de sincronia. Mitigação: usar modelo com word-level timestamps (whisperx ou Whisper "verbose_json") e revisar visualmente corte por corte.
- **Cortes não cabem em 60s** → conteúdo cortado no meio de uma fala. Mitigação: tolerância 50–75s e snapping em pausas de fala detectadas pela transcrição.
- **MCP Drive falha em uploads grandes** → bloqueio na publicação. Mitigação: capturar erros por arquivo, manter MP4 locais, permitir reupload manual.
- **Resolução do original muito grande (4K)** → render demorado. Mitigação: aceitar tempo de render mais longo (não redimensionar) e processar cortes em série.
- **Ícone/logo com canal alfa inesperado** → bordas brancas indesejadas. Mitigação: padrão com `format=rgba` no filtro e `pad=...:white` no outro.

## Migration Plan

Não há migração de sistemas existentes — é um pipeline novo, executado localmente. Em caso de erro detectado pós-upload, basta apagar o arquivo no Drive e refazer o corte específico.

## Open Questions

- Os títulos/slugs de cada corte (parte `<slug>`) virão do conteúdo (sugerido pela skill) ou serão definidos manualmente pelo operador? Decisão prática: a skill propõe, o operador confirma.
- A logo precisa ter algum espaçamento mínimo do quadro? Especificação atual diz "do tamanho do vídeo" — interpretado como `fit` preservando proporção, sem padding extra além do fundo branco que preenche o aspect ratio.
