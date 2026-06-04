## Why

A IBB precisa de 6 cortes curtos (≈1 min) extraídos do vídeo principal `EB5B4AAD-2E7B-412E-9A3B-10B0F49D8A19.MP4` para distribuição em redes sociais. Os clipes precisam de identidade visual consistente (ícone fixo, encerramento com logo) e legendas legíveis em vertical/horizontal, todos publicados na pasta `videos-ibb` do Google Drive da IBB.

## What Changes

- Selecionar 6 trechos coerentes do vídeo-fonte (cada um ~60s, com folga de ±10s quando o conteúdo exigir).
- Aplicar legendas burned-in em ASS/SSA com estilo bold-overlay (Antique Olive 14pt, branco, contorno preto Outline=1, Alignment=2, MarginV=90), chunking de 2 palavras por linha em MAIÚSCULAS.
- Sobrepor `icone.png` no canto superior esquerdo, em tamanho de ícone (≈80–96px), com margem mínima do topo e da esquerda (sem encostar nas bordas).
- Acrescentar 2 segundos finais com `logo.png` centralizada e dimensionada ao quadro, sobre fundo branco.
- Renderizar os 6 cortes em MP4 (H.264 + AAC) preservando resolução e proporção do vídeo-fonte.
- Fazer upload dos 6 MP4 finais para o Google Drive na pasta `videos-ibb` via MCP.

## Capabilities

### New Capabilities
- `video-cuts-ibb`: pipeline para gerar e publicar cortes editados do vídeo-fonte da IBB com legenda, ícone, encerramento e upload no Drive.

### Modified Capabilities
<!-- nenhum spec existente é alterado -->

## Impact

- Arquivos no diretório `/Users/jorgehbchaves/Dev/teste2/`:
  - Origem: `EB5B4AAD-2E7B-412E-9A3B-10B0F49D8A19.MP4`, `icone.png`, `logo.png`.
  - Saída local: 6 arquivos `corte-XX-<slug>.mp4` em uma pasta de trabalho (ex.: `output/cortes/`).
  - Artefatos intermediários: trilha de transcrição (Whisper/Outro) e arquivos `.ass` por corte.
- Ferramentas externas: `ffmpeg` (com libass), Whisper (ou equivalente para transcrição/timing), fonte Antique Olive disponível no sistema.
- Integrações: MCP Google Drive (`mcp__claude_ai_Google_Drive__*`) para upload na pasta `videos-ibb`.
- Skill: `/video-use` orquestra a edição; é necessário que o usuário a invoque na fase de apply.
