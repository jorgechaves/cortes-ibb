## ADDED Requirements

### Requirement: Sistema gera dez posts de Instagram por run
O módulo `instagram.generate` SHALL aceitar e retornar exatamente 10 posts quando chamado com 10 cortes.

#### Scenario: 10 cortes entregues ao gerador
- **WHEN** `generate(cuts)` é chamado com uma lista de 10 cortes
- **THEN** a função retorna uma lista de 10 `InstagramPost` válidos ou `None` em caso de falha

#### Scenario: Número incorreto de cortes
- **WHEN** `generate(cuts)` é chamado com qualquer número diferente de 10
- **THEN** a função loga "Pulando — esperava 10 cortes, vieram N" e retorna `None`

### Requirement: Schema JSON do LLM valida 10 posts
O JSON schema enviado ao OpenAI SHALL ter `minItems: 10, maxItems: 10` no array de posts.

#### Scenario: Resposta do LLM com menos de 10 posts
- **WHEN** o LLM retorna um JSON com menos de 10 posts (ex: falha de contexto)
- **THEN** `_validate` lança erro interno e o sistema tenta novamente (retry existente)

### Requirement: Arquivos de texto gerados para os 10 cortes
`write_files` SHALL gerar `corte-01-instagram.txt` a `corte-10-instagram.txt` e um `instagram.md` consolidado.

#### Scenario: Escrita bem-sucedida dos 10 arquivos
- **WHEN** `write_files(posts, cuts, out_dir)` é chamado com 10 posts
- **THEN** 10 arquivos `.txt` e 1 arquivo `.md` são criados na pasta de output
