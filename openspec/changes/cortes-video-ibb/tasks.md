## 1. Pré-condições do ambiente

- [ ] 1.1 Confirmar presença local de `EB5B4AAD-2E7B-412E-9A3B-10B0F49D8A19.MP4`, `icone.png` e `logo.png` em `/Users/jorgehbchaves/Dev/teste2/`
- [ ] 1.2 Verificar `ffmpeg` + `ffprobe` instalados (`ffmpeg -version`) com suporte a libass e libx264
- [ ] 1.3 Validar fonte Antique Olive (`fc-list | grep -i 'antique olive'`); se ausente, alinhar substituição com o operador antes de seguir
- [ ] 1.4 Criar pasta de trabalho `output/cortes/` e subpasta `output/cortes/work/` para artefatos intermediários (ass, outro-XX.mp4)
- [ ] 1.5 Rodar `ffprobe` no vídeo-fonte e registrar resolução (W×H), fps, duração, codecs — usado nos filtros de escala e no outro

## 2. Transcrição e seleção dos trechos (via `/video-use`)

- [ ] 2.1 Invocar `/video-use` apontando para o vídeo-fonte para obter transcrição com timestamps por palavra
- [ ] 2.2 Identificar 6 trechos coerentes alvo de ~60s (50–75s), com início/fim em pausas naturais; registrar `start_ts`/`end_ts` e tema (slug) de cada um
- [ ] 2.3 Salvar mapa dos cortes (`output/cortes/work/cuts.json`) com índice, slug, start, end e título legível
- [ ] 2.4 Revisar o mapa com o operador antes de renderizar

## 3. Geração das legendas ASS (1 por corte)

- [ ] 3.1 Para cada corte, recortar a transcrição entre `start_ts` e `end_ts` e rebasear os timestamps para começar em 0
- [ ] 3.2 Chunking: dividir em blocos com no máximo 2 palavras por linha, todas em MAIÚSCULAS
- [ ] 3.3 Renderizar arquivo `output/cortes/work/corte-XX.ass` com Style `Antique Olive`, 14pt, branco, Outline=1, Shadow=0, Alignment=2, MarginV=90
- [ ] 3.4 Validar visualmente uma prévia rápida (`ffplay` ou render de 5s) antes de processar os 6 finais

## 4. Cartão final (outro com logo.png)

- [ ] 4.1 Gerar `output/cortes/work/outro.mp4` (2s) com `logo.png` centralizada, fundo branco, mesma resolução/fps do vídeo-fonte, áudio silencioso AAC 48 kHz estéreo
- [ ] 4.2 Conferir que `outro.mp4` casa em resolução, fps e timebase com os cortes (para o concat funcionar sem reencode adicional)

## 5. Render dos 6 cortes principais

- [ ] 5.1 Para cada corte (01..06): cortar o trecho do vídeo-fonte com `-ss`/`-to` precisos, reencode H.264 + AAC
- [ ] 5.2 Aplicar filtro composto: `subtitles=corte-XX.ass` → `overlay` do ícone escalado (~88 px) em `x=36,y=36`
- [ ] 5.3 Conferir parâmetros: CRF 20, `preset medium`, `-pix_fmt yuv420p`, `-movflags +faststart`, áudio AAC 160 kbps 48 kHz estéreo
- [ ] 5.4 Salvar como `output/cortes/work/corte-XX-conteudo.mp4`

## 6. Concatenação com o cartão final

- [ ] 6.1 Criar `output/cortes/work/concat-XX.txt` listando `corte-XX-conteudo.mp4` e `outro.mp4`
- [ ] 6.2 Executar `ffmpeg -f concat -safe 0 -i concat-XX.txt -c copy output/cortes/corte-XX-<slug>.mp4`
- [ ] 6.3 Se o concat com `-c copy` falhar por diferenças de timebase, refazer com reencode (`-c:v libx264 -c:a aac`) mantendo os mesmos parâmetros

## 7. Validação dos arquivos finais

- [ ] 7.1 Rodar `ffprobe` em cada `corte-XX-<slug>.mp4` e confirmar codecs (H.264/AAC), resolução, fps e duração total (~62s)
- [ ] 7.2 Reprodução manual rápida (3–5s no meio e nos 2s finais) para confirmar legendas no rodapé, ícone no canto superior esquerdo e cartão final com logo
- [ ] 7.3 Registrar checksum (sha256) dos 6 arquivos finais em `output/cortes/work/checksums.txt`

## 8. Upload para Google Drive (MCP)

- [ ] 8.1 Localizar a pasta `videos-ibb` no Drive via `mcp__claude_ai_Google_Drive__search_files` (`mimeType='application/vnd.google-apps.folder'`)
- [ ] 8.2 Se a pasta não existir, parar e perguntar ao operador antes de criar nova
- [ ] 8.3 Para cada corte, chamar `mcp__claude_ai_Google_Drive__create_file` com `parents=[folderId]`, `name='corte-XX-<slug>.mp4'`, `mimeType='video/mp4'` e o conteúdo do arquivo local
- [ ] 8.4 Capturar o ID do Drive de cada upload e armazenar em `output/cortes/work/drive-ids.json`
- [ ] 8.5 Em caso de falha, listar arquivos afetados sem remover MP4 locais; tentar reupload apenas dos que falharam

## 9. Encerramento

- [ ] 9.1 Resumo final ao usuário: lista dos 6 nomes, durações, IDs no Drive e link para a pasta `videos-ibb`
- [ ] 9.2 Marcar a change como pronta para `/opsx:archive` quando o upload estiver confirmado
