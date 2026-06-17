# Spec: sermon-title-input

## Purpose

Captura o título do sermão no modal de processamento da interface web, persiste em `titulo.txt` no `job_dir`, e usa o slug do título nos nomes dos arquivos de corte gerados pelo pipeline.

## ADDED Requirements

### Requirement: Campo de título do sermão no modal de upload
O modal de opções de processamento SHALL exibir um campo de texto para o usuário digitar o título do sermão antes de confirmar o processamento. O campo SHALL ser exibido acima dos botões de escolha de modo (Com legenda / Sem legenda / Só transcrição). O preenchimento do campo é opcional — a ausência de título não bloqueia o processamento.

#### Scenario: Modal exibe campo de título
- **WHEN** o usuário arrasta ou seleciona um arquivo de vídeo
- **THEN** o modal de opções exibe um campo de texto com placeholder "Título do sermão (opcional)" acima dos botões de modo

#### Scenario: Título submetido junto com o upload
- **WHEN** o usuário preenche o título e clica em qualquer botão de modo
- **THEN** o frontend inclui o campo `titulo` com o valor digitado no FormData enviado a `POST /upload`

#### Scenario: Upload sem título preenche campo vazio
- **WHEN** o usuário deixa o campo de título vazio e clica em qualquer botão de modo
- **THEN** o frontend envia `titulo` como string vazia (ou ausente) e o processamento segue normalmente

### Requirement: Persistência do título no job_dir
A rota `POST /upload` SHALL aceitar o campo de formulário opcional `titulo: str` e, se não vazio após strip, salvar o valor em `output/{job_id}/titulo.txt` antes de disparar o pipeline. Se `titulo` estiver ausente ou vazio, `titulo.txt` NÃO é criado.

#### Scenario: titulo.txt criado quando título fornecido
- **WHEN** `POST /upload` é chamado com campo `titulo` não vazio (ex: "A Graça de Deus")
- **THEN** o arquivo `output/{job_id}/titulo.txt` é criado com o conteúdo "A Graça de Deus" antes de o pipeline iniciar

#### Scenario: titulo.txt não criado quando título ausente
- **WHEN** `POST /upload` é chamado sem campo `titulo` ou com `titulo` vazio
- **THEN** nenhum arquivo `titulo.txt` é criado e o pipeline executa com comportamento padrão

### Requirement: Nomes de cortes prefixados com slug do título
O pipeline SHALL prefixar os nomes dos arquivos de corte com o slug do título do sermão quando `titulo.txt` existir no `job_dir`. O slug SHALL ser gerado com: normalização Unicode NFD, remoção de diacríticos, lowercase, substituição de espaços e não-alfanuméricos por `-`, remoção de hifens consecutivos, truncado a 40 caracteres. O padrão de nome muda de `corte-{idx:02d}-{c.slug}.mp4` para `{titulo_slug}-corte-{idx:02d}-{c.slug}.mp4`.

#### Scenario: Cortes prefixados com slug do título
- **WHEN** `titulo.txt` existe no `job_dir` com conteúdo "A Graça de Deus"
- **THEN** os cortes são nomeados `a-graca-de-deus-corte-01-{slug}.mp4`, `a-graca-de-deus-corte-02-{slug}.mp4`, etc.

#### Scenario: Cortes sem prefixo quando título ausente
- **WHEN** `titulo.txt` não existe no `job_dir`
- **THEN** os cortes são nomeados `corte-01-{slug}.mp4` conforme comportamento atual

#### Scenario: Slug truncado para título longo
- **WHEN** `titulo.txt` contém um título com mais de 40 caracteres após slugificação
- **THEN** o slug é truncado a 40 caracteres (sem cortar no meio de uma palavra não é obrigatório) e o nome do corte usa esse slug truncado

#### Scenario: Nomes de cortes no Drive incorporam o título
- **WHEN** os cortes são enviados ao Google Drive após o pipeline
- **THEN** os arquivos no Drive têm nomes com o prefixo do título (ex: `a-graca-de-deus-corte-01-slug.mp4`) pois o Drive usa o nome do arquivo local
