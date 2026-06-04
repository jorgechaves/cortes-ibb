## ADDED Requirements

### Requirement: Inicialização single-command
A aplicação SHALL ser iniciada por um único comando `python3 app.py` a partir do diretório do projeto. Na inicialização, o servidor SHALL escolher uma porta livre (preferindo `7860`; se ocupada, tentar `7861`–`7870`) e SHALL abrir automaticamente o navegador padrão do sistema na URL local. O processo SHALL permanecer ativo até `Ctrl+C` ou até o usuário clicar em "Encerrar" na UI.

#### Scenario: Início padrão
- **WHEN** o operador executa `python3 app.py`
- **THEN** o servidor escuta em `127.0.0.1:<porta>`, imprime a URL no stdout e o navegador padrão é aberto na URL

#### Scenario: Porta ocupada
- **WHEN** a porta `7860` está em uso
- **THEN** o servidor tenta as próximas portas em sequência (`7861`–`7870`) e usa a primeira livre

### Requirement: Interface drag-and-drop
A UI servida em `GET /` SHALL apresentar uma drop zone central aceitando arquivos `video/mp4` (e `.mov`, `.m4v`) por drag-and-drop ou clique. A UI SHALL rejeitar localmente arquivos não-vídeo antes do upload, exibindo mensagem de erro. Apenas um upload por vez SHALL ser aceito; enquanto um processamento está em andamento, a drop zone SHALL ser desabilitada.

#### Scenario: Arrastar vídeo válido
- **WHEN** o operador arrasta um `.MP4` para a drop zone
- **THEN** a UI mostra o nome do arquivo, inicia o upload e troca o estado para "Enviando..."

#### Scenario: Arquivo inválido
- **WHEN** o operador arrasta um `.txt` ou imagem
- **THEN** a UI exibe "Tipo de arquivo não suportado" e não inicia upload

#### Scenario: Upload concorrente
- **WHEN** um processamento já está em andamento e o operador tenta soltar outro vídeo
- **THEN** a UI ignora o segundo arquivo e mostra "Aguarde o processo atual terminar"

### Requirement: Barra de progresso por estágio
A UI SHALL exibir uma barra de progresso global (0–100%) que reflete o avanço ponderado dos estágios: `upload (5%)`, `probe (2%)`, `transcrição (25%)`, `seleção dos cortes (3%)`, `legendas ASS (5%)`, `cartão final (5%)`, `render dos 6 cortes (40%)`, `concat (5%)`, `upload Drive (10%)`. A UI SHALL mostrar o rótulo do estágio atual e um sub-progresso quando aplicável (ex.: "Renderizando corte 3 de 6 — 47%").

#### Scenario: Avanço durante render
- **WHEN** o backend está renderizando o corte 3 de 6 e o ffmpeg reporta 47% desse corte
- **THEN** a barra global mostra `5 + 2 + 25 + 3 + 5 + 5 + (2/6)*40 + (0.47 * 1/6)*40 ≈ 51%` e o rótulo "Renderizando corte 3 de 6 — 47%"

#### Scenario: Conclusão
- **WHEN** todos os estágios terminam com sucesso (inclusive upload no Drive)
- **THEN** a barra mostra 100%, o rótulo muda para "Concluído" e a UI lista os 6 arquivos com IDs do Drive

### Requirement: Streaming de eventos via SSE
O backend SHALL expor `GET /events` como Server-Sent Events. Para cada evento emitido pelo pipeline, o servidor SHALL enviar um payload JSON com campos `type` (`progress`|`stage`|`log`|`done`|`error`), `percent` (0–100, quando aplicável), `stage` (string), `message` (string), `data` (objeto opcional). A UI SHALL reconectar automaticamente ao stream em caso de queda durante o processamento.

#### Scenario: Evento de progresso
- **WHEN** o backend completa um sub-estágio
- **THEN** envia `{"type":"progress","percent":<n>,"stage":"<id>","message":"<texto>"}` pelo stream SSE

#### Scenario: Erro
- **WHEN** o pipeline falha em qualquer estágio
- **THEN** o backend envia `{"type":"error","stage":"<id>","message":"<motivo>"}` e a UI exibe um banner vermelho com a mensagem e botão "Tentar novamente"

### Requirement: Endpoint de upload
O backend SHALL aceitar `POST /upload` como `multipart/form-data` com campo `video`. O servidor SHALL salvar o arquivo em `output/<job-id>/source.mp4`, criar um job ID curto (timestamp + slug random) e iniciar o pipeline em background. A resposta SHALL ser JSON `{"jobId":"<id>","stream":"/events?jobId=<id>"}`.

#### Scenario: Upload aceito
- **WHEN** a UI envia o vídeo via POST /upload
- **THEN** o servidor responde 200 com o JSON do jobId e dispara o pipeline em uma thread/processo de trabalho

#### Scenario: Vídeo muito grande
- **WHEN** o upload excede 5 GB
- **THEN** o servidor responde 413 e a UI exibe "Arquivo excede 5 GB — comprima antes"

### Requirement: Orquestração programática do pipeline
O app SHALL invocar o pipeline `video-cuts-ibb` através de uma API Python (módulo `pipeline`) que aceita o caminho do vídeo-fonte, caminhos de `icone.png` e `logo.png`, diretório de saída, e um callback `on_event(event: dict)`. Cada estágio do pipeline SHALL emitir eventos via esse callback. O pipeline SHALL ser executável **sem nenhuma interação humana** (modo totalmente automático).

#### Scenario: Pipeline emite eventos
- **WHEN** o app chama `pipeline.run(source=..., on_event=cb)`
- **THEN** o callback é invocado pelo menos uma vez por estágio com `type='stage'` e múltiplas vezes com `type='progress'` durante render e upload

#### Scenario: Modo headless
- **WHEN** o pipeline é executado sem UI (via app rodando)
- **THEN** os 6 cortes são selecionados, renderizados e enviados ao Drive sem qualquer prompt interativo

### Requirement: Resultado final visível na UI
Ao terminar com sucesso, a UI SHALL exibir uma lista dos 6 cortes com: nome do arquivo local, duração, link clicável para o arquivo no Drive (URL `https://drive.google.com/file/d/<id>/view`) e botão "Abrir pasta local" que aponta para `output/<job-id>/`. A UI SHALL persistir esse resultado até o operador soltar um novo vídeo na drop zone.

#### Scenario: Lista de resultados
- **WHEN** o pipeline finaliza
- **THEN** a UI renderiza 6 linhas com `corte-XX-<slug>.mp4`, duração `~62s`, link para o Drive e botão de abrir pasta

### Requirement: Setup automático na primeira execução
Na primeira execução, o app SHALL: (a) verificar `ffmpeg`/`ffprobe` no PATH e abortar com mensagem clara se ausentes; (b) verificar a fonte Antique Olive e avisar (não bloquear) caso ausente, oferecendo cair em fallback `Arial Black`; (c) se as credenciais do Google Drive não existirem em `~/.config/cortes-ibb/`, iniciar o fluxo OAuth abrindo o navegador para autorização e armazenar `token.json` para reuso.

#### Scenario: Primeira execução sem token Drive
- **WHEN** `~/.config/cortes-ibb/token.json` não existe
- **THEN** o app abre o navegador para o consent do Google, salva o token e segue para a UI principal

#### Scenario: ffmpeg ausente
- **WHEN** `ffmpeg` não está no PATH
- **THEN** o app imprime instrução de instalação e encerra com código `2`, sem subir o servidor
