## MODIFIED Requirements

### Requirement: Seleção dos 6 cortes
O sistema SHALL produzir exatamente 6 cortes a partir do vídeo-fonte fornecido pelo operador via UI. Cada corte SHALL ter duração-alvo de 60 segundos, com tolerância permitida entre 50 e 75 segundos quando necessário para preservar coerência semântica (início e fim em fronteiras naturais de fala detectadas pela transcrição). A seleção SHALL ser **totalmente automática** — o backend escolhe os 6 melhores trechos sem prompts interativos, usando a transcrição com timestamps de palavras para priorizar pausas longas (>500 ms) como fronteiras. Os cortes SHALL ser numerados `corte-01` a `corte-06` e nomeados como `corte-XX-<slug>.mp4`, com `<slug>` derivado das palavras-chave do trecho.

#### Scenario: Corte dentro da tolerância
- **WHEN** o backend escolhe um trecho a partir da transcrição
- **THEN** o trecho gera um MP4 com duração entre 50s e 75s, com fronteiras coincidindo com pausas detectadas de pelo menos 500 ms

#### Scenario: Quantidade exata
- **WHEN** o pipeline termina
- **THEN** existem 6 arquivos MP4 finais, com prefixos `corte-01-` a `corte-06-` e sufixo `.mp4`

#### Scenario: Sem intervenção humana
- **WHEN** o app recebe o vídeo e dispara o pipeline
- **THEN** os 6 trechos são selecionados, renderizados e enviados ao Drive sem qualquer prompt ou pausa para revisão

### Requirement: Upload para Google Drive
O sistema SHALL fazer upload dos 6 arquivos finais para a pasta `videos-ibb` no Google Drive. O acesso SHALL usar a **Google Drive API com OAuth de usuário**, com credenciais armazenadas localmente em `~/.config/cortes-ibb/` (`credentials.json` + `token.json`). Cada upload SHALL preservar o nome local `corte-XX-<slug>.mp4` e o tipo MIME `video/mp4`. Em caso de falha de upload, o sistema SHALL reportar via callback de evento quais cortes falharam e SHALL manter os arquivos locais intactos.

#### Scenario: Upload com sucesso via OAuth
- **WHEN** o token OAuth é válido e a pasta `videos-ibb` é localizada (`q="name='videos-ibb' and mimeType='application/vnd.google-apps.folder'"`)
- **THEN** os 6 arquivos são enviados via `files.create` resumable, com `name` preservado e `mimeType='video/mp4'`, e os IDs do Drive são reportados via evento `done`

#### Scenario: Token expirado
- **WHEN** o token armazenado expirou e há refresh_token válido
- **THEN** o cliente atualiza silenciosamente o access_token e prossegue com o upload

#### Scenario: Falha em upload
- **WHEN** o upload de um ou mais cortes falha (timeout, 5xx, sem rede)
- **THEN** o pipeline emite evento `error` listando os arquivos afetados, mantém todos os MP4 locais e oferece retry via UI
