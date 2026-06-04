## ADDED Requirements

### Requirement: Seleção dos 6 cortes
O sistema SHALL produzir exatamente 6 cortes a partir do vídeo-fonte `EB5B4AAD-2E7B-412E-9A3B-10B0F49D8A19.MP4`. Cada corte SHALL ter duração-alvo de 60 segundos, com tolerância permitida entre 50 e 75 segundos quando necessário para preservar coerência semântica (início e fim em fronteiras naturais de fala). Os cortes SHALL ser numerados de `corte-01` a `corte-06` e nomeados como `corte-XX-<slug>.mp4`, onde `<slug>` é um kebab-case derivado do tema do trecho.

#### Scenario: Corte dentro da tolerância
- **WHEN** o operador identifica um trecho coerente de ~60s no vídeo-fonte
- **THEN** o sistema gera um arquivo MP4 com duração entre 50s e 75s, iniciando e terminando em pausas naturais de fala

#### Scenario: Quantidade exata
- **WHEN** o pipeline termina
- **THEN** existem 6 arquivos MP4 finais, com prefixos `corte-01-` a `corte-06-` e sufixo `.mp4`

### Requirement: Estilo das legendas burned-in
O sistema SHALL gerar legendas queimadas no vídeo a partir da transcrição do áudio do trecho. As legendas SHALL usar fonte Antique Olive, tamanho 14pt, cor branca (`&H00FFFFFF`), contorno preto com Outline=1, Shadow=0, Alignment=2 (rodapé centralizado) e MarginV=90. Cada bloco exibido SHALL conter no máximo 2 palavras por linha, todas em MAIÚSCULAS, sincronizadas com a fala correspondente.

#### Scenario: Renderização da legenda
- **WHEN** o ffmpeg aplica o filtro de legenda ASS sobre um corte
- **THEN** o vídeo exibe textos em MAIÚSCULO, brancos com contorno preto fino, posicionados no rodapé respeitando MarginV=90 e com no máximo 2 palavras por linha

#### Scenario: Sincronização com a fala
- **WHEN** uma palavra é pronunciada no áudio
- **THEN** ela aparece na legenda dentro de uma janela máxima de ±150 ms em relação ao seu timestamp original

### Requirement: Ícone fixo no canto superior esquerdo
O sistema SHALL sobrepor `icone.png` no canto superior esquerdo de cada corte, escalado a aproximadamente 80–96 px de altura (tamanho de ícone). O ícone SHALL ter margem do topo e da esquerda de pelo menos 24 px, de forma a não tocar nas bordas do vídeo. O ícone SHALL permanecer visível durante toda a duração do conteúdo principal do corte (excluindo o cartão final de logo).

#### Scenario: Posicionamento do ícone
- **WHEN** o vídeo é renderizado
- **THEN** `icone.png` aparece no canto superior esquerdo a >= 24 px de distância das bordas superior e esquerda, com altura entre 80 e 96 px

#### Scenario: Ícone oculto no cartão final
- **WHEN** o cartão final de logo é exibido
- **THEN** `icone.png` não está visível durante esses 2 segundos finais

### Requirement: Cartão final com logo
Cada corte SHALL terminar com exatamente 2 segundos de um cartão estático contendo `logo.png` centralizada sobre fundo branco. A logo SHALL ser escalada para caber no quadro preservando a proporção (`fit`), ocupando o maior tamanho possível sem ultrapassar as bordas do vídeo. O cartão SHALL usar a mesma resolução, framerate e codec do conteúdo principal.

#### Scenario: Duração e composição do cartão final
- **WHEN** o reprodutor chega aos 2 segundos finais
- **THEN** o quadro mostra fundo branco com `logo.png` centralizada, ocupando o quadro inteiro respeitando a proporção, sem áudio sobreposto adicional

### Requirement: Parâmetros técnicos de saída
Os cortes finais SHALL ser codificados em H.264 (vídeo) e AAC (áudio), com a mesma resolução e framerate do vídeo-fonte. O bitrate de vídeo SHALL produzir qualidade visualmente equivalente ao original (CRF 18–23 com libx264 ou equivalente). O áudio SHALL ser 48 kHz estéreo, 128–192 kbps.

#### Scenario: Inspeção do MP4 final
- **WHEN** um corte final é inspecionado com `ffprobe`
- **THEN** o vídeo é H.264, o áudio é AAC, e a resolução e framerate coincidem com os do vídeo-fonte

### Requirement: Upload para Google Drive
O sistema SHALL fazer upload dos 6 arquivos finais para a pasta `videos-ibb` no Google Drive conectado via MCP. Cada upload SHALL preservar o nome local `corte-XX-<slug>.mp4` e o tipo MIME `video/mp4`. Em caso de falha de upload, o sistema SHALL reportar qual(is) corte(s) falhou(aram) e manter os arquivos locais intactos.

#### Scenario: Upload com sucesso
- **WHEN** os 6 MP4 estão prontos e a pasta `videos-ibb` é localizada no Drive
- **THEN** os 6 arquivos são enviados, com nomes preservados e tipo MIME `video/mp4`, e seus IDs do Drive são reportados

#### Scenario: Falha em upload
- **WHEN** o upload de um ou mais cortes falha
- **THEN** o sistema relata os arquivos afetados, mantém todos os MP4 locais, e não remove arquivos parciais do Drive sem confirmação
