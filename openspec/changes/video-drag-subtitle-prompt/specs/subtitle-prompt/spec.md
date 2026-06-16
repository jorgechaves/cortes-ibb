## ADDED Requirements

### Requirement: Modal de escolha de legenda antes do upload
O sistema SHALL exibir um modal de confirmação após o usuário arrastar um vídeo para a dropzone ou selecioná-lo via file picker, antes de iniciar o upload. O modal SHALL apresentar duas opções: "Sim, com legenda" e "Não, sem legenda". O upload SHALL ser iniciado apenas após o usuário fazer uma escolha explícita.

#### Scenario: Usuário arrasta vídeo e escolhe com legenda
- **WHEN** o usuário arrasta um arquivo de vídeo para a dropzone
- **THEN** o modal de escolha de legenda é exibido com as opções "Sim, com legenda" e "Não, sem legenda"
- **THEN** ao clicar em "Sim, com legenda" o modal fecha e o upload inicia com `subtitle=true`

#### Scenario: Usuário arrasta vídeo e escolhe sem legenda
- **WHEN** o usuário arrasta um arquivo de vídeo para a dropzone
- **THEN** o modal de escolha de legenda é exibido
- **THEN** ao clicar em "Não, sem legenda" o modal fecha e o upload inicia com `subtitle=false`

#### Scenario: Usuário seleciona vídeo via file picker e vê o modal
- **WHEN** o usuário clica na dropzone e seleciona um arquivo via file picker do sistema operacional
- **THEN** o modal de escolha de legenda é exibido antes do upload iniciar

#### Scenario: Usuário fecha o modal sem escolher
- **WHEN** o modal está aberto e o usuário clica fora dele ou pressiona Escape
- **THEN** o modal é fechado sem iniciar o upload
- **THEN** a dropzone volta ao estado idle
