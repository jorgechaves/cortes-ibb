## ADDED Requirements

### Requirement: Geração de pacote de feed por corte
O sistema SHALL gerar, para cada um dos 6 cortes de um job, um pacote de texto de feed Instagram contendo: `hook` (≤ 80 caracteres, 1 linha), `caption` (3–6 parágrafos curtos em PT-BR), `cta` (chamada padronizada), `hashtags` (10 a 15 tags em PT-BR, sem `#` duplicado, mistura de amplas e nichadas). A geração SHALL usar o modelo OpenAI configurado (default `gpt-4o-mini`), em uma única chamada que recebe os 6 cortes (com `title`, `rationale` e texto transcrito) e devolve os 6 pacotes em JSON. A geração SHALL ocorrer no estágio `instagram` do pipeline, entre `concat` e `drive`.

#### Scenario: Geração bem-sucedida
- **WHEN** o estágio `instagram` é executado com `OPENAI_API_KEY` configurada
- **THEN** o pipeline emite eventos `progress` para o estágio `instagram` e, ao final, cada um dos 6 cortes tem um pacote com `hook`, `caption`, `cta` e `hashtags` válidos

#### Scenario: Validação do conteúdo
- **WHEN** o LLM retorna o JSON
- **THEN** o sistema valida que existem 6 entradas (uma por corte), cada `hook` ≤ 80 caracteres, cada `caption` ≥ 1 parágrafo, cada lista de hashtags entre 10 e 15 entradas, e ignora `#` duplicado (case-insensitive)

#### Scenario: Trunca campos longos
- **WHEN** o LLM devolve `hook` com mais de 80 caracteres ou `hashtags` acima de 15
- **THEN** o sistema trunca silenciosamente para o limite (80 chars / 15 hashtags) sem abortar o job

### Requirement: Persistência local dos textos
Para cada job, o sistema SHALL gravar, em `output/<job-id>/`:

- `instagram.md` — arquivo Markdown único com os 6 posts em ordem (`## 1. <title>` → hook em negrito → caption → CTA em itálico → hashtags em bloco code).
- `corte-XX-instagram.txt` — um arquivo de texto puro por corte (`XX` = 01..06), formatado para copy-paste direto no Instagram: hook + linha em branco + caption + linha em branco + CTA + linha em branco + hashtags separadas por espaço.

#### Scenario: Arquivos gerados localmente
- **WHEN** o estágio `instagram` termina com sucesso
- **THEN** existem 7 arquivos novos em `output/<job-id>/`: um `instagram.md` e seis `corte-01-instagram.txt` a `corte-06-instagram.txt`

### Requirement: Upload das legendas para o Drive
O sistema SHALL fazer upload dos arquivos de legenda (`instagram.md` + `corte-XX-instagram.txt`) para a mesma subpasta `videos-ibb/[YYYY-MM-DD]` onde os MP4 são enviados, com `mimeType='text/markdown'` para o `.md` e `mimeType='text/plain'` para os `.txt`.

#### Scenario: Upload conjunto com os MP4
- **WHEN** todos os MP4 e legendas estão prontos
- **THEN** a subpasta no Drive contém 13 arquivos (6 MP4 + 6 TXT + 1 MD), e a UI lista os links dos MP4 com os textos exibidos

### Requirement: Fallback sem custo de bloqueio
Se `OPENAI_API_KEY` está ausente OU se a chamada à API falha duas vezes seguidas, o estágio `instagram` SHALL ser pulado silenciosamente (com um evento `log` de aviso), e o pipeline SHALL continuar normalmente (upload dos MP4 sem legendas).

#### Scenario: Sem API key
- **WHEN** o pipeline chega no estágio `instagram` e `OPENAI_API_KEY` não está definida
- **THEN** o estágio emite `log` "Pulando geração de legendas — OPENAI_API_KEY ausente" e segue para o estágio `drive` sem abortar

#### Scenario: Falha de API persistente
- **WHEN** a chamada para gerar legendas falha duas vezes
- **THEN** o estágio emite `log` com o motivo, marca `instagram_skipped=true` no resultado, e o pipeline continua

### Requirement: Exibição na UI com botão Copiar
Quando o pipeline termina, a UI SHALL renderizar, para cada corte, uma seção expansível com os 4 campos do pacote (hook, caption, CTA, hashtags). Cada corte SHALL ter um botão **Copiar** que coloca no clipboard o conteúdo formatado para Instagram (mesmo formato do `corte-XX-instagram.txt`).

#### Scenario: Botão Copiar
- **WHEN** o operador clica em **Copiar** ao lado de um corte
- **THEN** o clipboard recebe o texto completo formatado (hook + caption + CTA + hashtags) e o botão mostra confirmação visual ("Copiado!") por ~1,5 s

#### Scenario: Quando legendas foram puladas
- **WHEN** o resultado vem com `instagram_skipped=true`
- **THEN** a UI exibe um aviso amarelo no topo da lista de cortes ("Legendas de Instagram não foram geradas — <motivo>") e não renderiza as seções de legenda
