## ADDED Requirements

### Requirement: Salvar transcrição completa em arquivo .txt
Após a transcrição, o sistema SHALL salvar um arquivo `transcript.txt` na pasta do job contendo o texto corrido completo de todas as palavras. Palavras separadas por silêncio superior a 1,5 s SHALL ser separadas por uma linha em branco no arquivo, para melhorar a legibilidade.

#### Scenario: Transcrição com fala contínua
- **WHEN** a transcrição é concluída com palavras sem pausas longas
- **THEN** `transcript.txt` é criado na pasta do job com todas as palavras unidas por espaços em um bloco único

#### Scenario: Transcrição com pausas longas
- **WHEN** a transcrição contém palavras com intervalo superior a 1,5 s entre si
- **THEN** `transcript.txt` separa os trechos com uma linha em branco no ponto de pausa

#### Scenario: Transcrição vazia
- **WHEN** nenhuma palavra é detectada na transcrição
- **THEN** `transcript.txt` é criado vazio na pasta do job sem erros

### Requirement: Incluir transcript.txt no upload ao Drive
O pipeline SHALL incluir `transcript.txt` na lista de arquivos enviados ao Google Drive após o processamento. O resultado do job SHALL conter `transcript_drive_url` com a URL pública do arquivo, ou `null` se o upload falhar ou o Drive não estiver configurado.

#### Scenario: Drive configurado e upload bem-sucedido
- **WHEN** o job é concluído com Drive configurado
- **THEN** `transcript.txt` é enviado ao Drive junto com os vídeos
- **THEN** o resultado inclui `transcript_drive_url` com a URL do arquivo no Drive

#### Scenario: Drive não configurado ou upload falha
- **WHEN** o Drive não está configurado ou o upload falha
- **THEN** `transcript_drive_url` no resultado é `null`
- **THEN** o pipeline não lança erro por causa do arquivo de transcrição

### Requirement: Exibir link do transcript.txt nos resultados da UI
Quando `transcript_drive_url` estiver presente no resultado, a UI SHALL exibir um link para o arquivo na seção de resultados, ao lado dos links dos vídeos.

#### Scenario: transcript_drive_url disponível
- **WHEN** o resultado do job contém `transcript_drive_url` não nulo
- **THEN** a UI exibe um botão/link "Transcrição" apontando para a URL do Drive

#### Scenario: transcript_drive_url ausente
- **WHEN** o resultado do job não contém `transcript_drive_url` ou o valor é null
- **THEN** a UI não exibe nenhum elemento de link de transcrição
