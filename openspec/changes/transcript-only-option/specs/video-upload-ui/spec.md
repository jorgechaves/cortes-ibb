## ADDED Requirements

### Requirement: UI exibe dois botões de ação após seleção de vídeo
A interface SHALL exibir dois botões de ação após o usuário arrastar ou selecionar um arquivo de vídeo: "Gerar Cortes" (modo atual) e "Só Transcrição" (novo modo).

#### Scenario: Botões aparecem após seleção de arquivo
- **WHEN** o usuário arrasta um arquivo de vídeo para a área de drop ou clica para selecionar
- **THEN** a UI SHALL exibir dois botões: "Gerar Cortes" e "Só Transcrição"
- **THEN** ambos os botões SHALL estar habilitados enquanto nenhum job estiver em execução

#### Scenario: Clique em "Gerar Cortes" envia modo cuts
- **WHEN** o usuário clica em "Gerar Cortes"
- **THEN** a UI SHALL enviar POST /upload com `mode=cuts` (ou sem o campo `mode`)
- **THEN** o checkbox de legenda SHALL ser incluído no FormData conforme seu estado atual

#### Scenario: Clique em "Só Transcrição" envia modo transcript
- **WHEN** o usuário clica em "Só Transcrição"
- **THEN** a UI SHALL enviar POST /upload com `mode=transcript`
- **THEN** a UI SHALL exibir a barra de progresso com os estágios de transcrição

### Requirement: Checkbox de legenda é ocultado no fluxo de transcrição
O checkbox "Legenda" não é relevante para o modo "Só Transcrição" e SHALL ser ocultado ou desabilitado quando o usuário iniciar um job nesse modo.

#### Scenario: Checkbox visível no modo padrão
- **WHEN** o usuário visualiza a tela de upload sem ter iniciado nenhum job
- **THEN** o checkbox de legenda SHALL estar visível

#### Scenario: Legenda ignorada no modo transcrição
- **WHEN** o usuário clica em "Só Transcrição"
- **THEN** o valor do checkbox de legenda SHALL ser ignorado pelo backend (não afeta o resultado)

### Requirement: Tela de resultado exibe link do transcript no modo transcrição
Após a conclusão de um job no modo transcrição, a UI SHALL exibir uma tela de resultado com links para acessar o `transcript.txt`.

#### Scenario: Resultado com link de download local
- **WHEN** o job de transcrição conclui com sucesso
- **THEN** a UI SHALL exibir um link para download do `transcript.txt` via `/files/{job_id}/transcript.txt`
- **THEN** a UI SHALL NOT exibir seção de cortes de vídeo

#### Scenario: Resultado com link do Drive quando disponível
- **WHEN** o job de transcrição conclui com sucesso e `transcript_drive_url` está presente no resultado
- **THEN** a UI SHALL exibir um link abrindo o arquivo no Google Drive
