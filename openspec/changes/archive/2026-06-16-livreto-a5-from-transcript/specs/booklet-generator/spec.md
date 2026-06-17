## ADDED Requirements

### Requirement: Geração de livreto A5 em PDF a partir do transcript
O sistema SHALL gerar um arquivo PDF no formato A5 (148 × 210 mm) a partir do arquivo `transcript.txt` de um job existente. O conteúdo textual SHALL ter ortografia e concordância corrigidas em português brasileiro antes de ser incluído no PDF. O sistema NÃO DEVE resumir, omitir ou reorganizar o conteúdo do transcript.

#### Scenario: Livreto gerado com sucesso
- **WHEN** `POST /booklet/{job_id}` é chamado e `output/{job_id}/transcript.txt` existe
- **THEN** o sistema corrige o texto via OpenAI, gera `output/{job_id}/livreto.pdf` em A5, e emite eventos SSE de progresso até `type: done`

#### Scenario: Transcript não encontrado
- **WHEN** `POST /booklet/{job_id}` é chamado e `output/{job_id}/transcript.txt` não existe
- **THEN** a rota retorna HTTP 404 com mensagem `transcript.txt não encontrado para o job {job_id}`

#### Scenario: Job não existe
- **WHEN** `POST /booklet/{job_id}` é chamado com um `job_id` que não corresponde a nenhuma pasta em `output/`
- **THEN** a rota retorna HTTP 404

### Requirement: Capa e contracapa com ícone
O PDF gerado SHALL conter uma página de capa e uma página de contracapa, cada uma exibindo `icone.png` centralizado na página A5. O título do sermão (extraído da primeira frase do transcript, truncado a 80 caracteres) SHALL aparecer na capa abaixo do ícone.

#### Scenario: Capa com ícone e título
- **WHEN** o livreto é gerado
- **THEN** a primeira página é A5 com `icone.png` centralizado horizontalmente, título do sermão abaixo do ícone, e margens de 15mm

#### Scenario: Contracapa com ícone
- **WHEN** o livreto é gerado
- **THEN** a última página é A5 com `icone.png` centralizado horizontalmente e verticalmente, sem texto adicional

### Requirement: Layout de conteúdo seguindo PDFs de referência
As páginas de conteúdo do livreto SHALL seguir o layout dos PDFs em `ebook/`: fonte serifada de 11pt, margens de 15mm em todos os lados, espaçamento entre linhas de 1.3×, texto justificado, numeração de páginas no rodapé centralizada.

#### Scenario: Texto paginado corretamente
- **WHEN** o livreto é gerado com um transcript longo
- **THEN** o texto flui por múltiplas páginas A5 com quebras automáticas, respeitando as margens de 15mm

#### Scenario: Numeração de páginas
- **WHEN** o livreto é gerado
- **THEN** todas as páginas de conteúdo (exceto capa e contracapa) exibem número de página centralizado no rodapé

### Requirement: Correção de português brasileiro em chunks
O sistema SHALL enviar o transcript ao OpenAI (`gpt-4o-mini`) em chunks de até 1.500 palavras para corrigir ortografia e concordância em português brasileiro, sem resumir o conteúdo. Se a correção falhar (timeout, quota ou indisponibilidade de API), o sistema SHALL usar o texto original sem correção e emitir um aviso via SSE.

#### Scenario: Correção bem-sucedida
- **WHEN** OPENAI_API_KEY está configurada e a API responde
- **THEN** o texto corrigido é usado no PDF e o sistema emite `type: log, message: "Texto corrigido em N chunks"`

#### Scenario: Fallback sem API key
- **WHEN** OPENAI_API_KEY não está configurada
- **THEN** o texto original é usado sem correção e o sistema emite `type: log, message: "OPENAI_API_KEY ausente — usando texto original"`

#### Scenario: Fallback por erro de API
- **WHEN** a chamada à API OpenAI falha (timeout ou erro)
- **THEN** o chunk falho é incluído sem correção, o sistema continua com os demais chunks e emite um aviso

### Requirement: Botão "Gerar Livreto" na interface web
A interface web SHALL exibir um botão "Gerar Livreto" na seção de resultados após a conclusão de qualquer job que produza `transcript.txt`. O botão SHALL disparar `POST /booklet/{job_id}` e exibir progresso via SSE na mesma área de log.

#### Scenario: Botão habilitado após job concluído
- **WHEN** o job termina com status `done` e o resultado inclui `transcript_local_path`
- **THEN** o botão "Gerar Livreto" é exibido e clicável na seção de resultados

#### Scenario: Estado de carregamento durante geração
- **WHEN** o usuário clica em "Gerar Livreto"
- **THEN** o botão fica desabilitado e a área de log exibe eventos de progresso em tempo real

#### Scenario: Conclusão da geração
- **WHEN** a geração do livreto termina com sucesso
- **THEN** a interface exibe um link para download do `livreto.pdf` e um link para o Drive (se disponível)
