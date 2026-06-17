## Context

O fluxo atual: usuário arrasta o vídeo → modal "subtitle-overlay" pergunta se quer legendas, sem legendas, ou só transcrição → frontend faz `POST /upload` com `file`, `subtitle`, e `mode`. O backend salva o vídeo em `output/{job_id}/`, executa o pipeline e gera cortes nomeados `corte-{idx:02d}-{c.slug}.mp4`. O livreto é gerado separadamente via `POST /booklet/{job_id}`, onde `generate_booklet()` extrai o título do texto corrigido com `_extract_title()` e salva o PDF como `livreto.pdf`.

Nenhuma das etapas sabe o nome real do sermão: os cortes têm nomes genéricos e o título extraído do transcript é heurístico.

## Goals / Non-Goals

**Goals:**
- Capturar o título do sermão no modal de upload (uma única interação extra, no momento certo)
- Persistir o título como `titulo.txt` no `job_dir` para ser consumido por pipeline e booklet
- Prefixar os arquivos de corte com slug do título: `{titulo_slug}-corte-{idx:02d}-{c.slug}.mp4`
- Usar `titulo.txt` como fonte de verdade do título no livreto (capa, cabeçalho, nome do PDF)
- Fallback gracioso quando título não é fornecido (comportamento atual preservado)

**Non-Goals:**
- Renomear a pasta do job (ainda usa `{job_id}` baseado em timestamp)
- Alterar a estrutura de `cuts.json`
- Renomear a pasta de destino no Google Drive (subfolder continua sendo `{job_id}`)
- Validação server-side do conteúdo do título (campo de texto livre)

## Decisions

### 1. Campo de título no modal existente (não um novo modal)

O campo de texto para o título é adicionado dentro do `#subtitle-overlay` existente, acima dos botões de escolha de modo. Alternativa descartada: novo modal antes do subtitle-overlay — criaria dois cliques onde hoje há um, e duplicaria estado JS.

### 2. `titulo.txt` como arquivo de persistência

O título é salvo como `output/{job_id}/titulo.txt` imediatamente no início do upload (no `POST /upload`), antes de o pipeline ser disparado em thread. O pipeline e o booklet leem de lá. Alternativa descartada: passar o título como parâmetro pela cadeia de funções — exigiria mudança de assinatura em várias camadas sem ganho real.

### 3. Prefixo no nome dos cortes, não sufixo

O padrão passa de `corte-01-slug.mp4` para `titulo-slug-corte-01-slug.mp4`. Prefixo garante agrupamento natural por sermão quando o Drive ou o Finder ordena por nome. Alternativa descartada: sufixo — os arquivos não se agrupam por sermão em listagem alfabética.

### 4. Slug para nomes de arquivo

O título é slugificado (lowercase, espaços → `-`, remoção de caracteres especiais) para compor nomes de arquivo seguros no S.O. e no Drive. O título original é preservado inteiro em `titulo.txt` para uso em texto (capa do livreto, cabeçalho de página). A função `_slugify(titulo)` fica em `pipeline/__init__.py` e é reutilizada pelo booklet.

### 5. Nome do PDF incorpora o título

O PDF muda de `livreto.pdf` para `livreto-{titulo_slug}.pdf`. O upload para Drive (`upload_booklet_to_drive`) já usa `Path(pdf_path).name`, então o Drive recebe o nome correto automaticamente sem alterar `drive.py`.

### 6. Booklet lê `titulo.txt`; `_extract_title()` como fallback

`generate_booklet()` tenta ler `titulo.txt` do `job_dir`. Se encontrar e não estiver vazio, usa o valor como título. Caso contrário, mantém a extração heurística atual via `_extract_title()`. Isso garante compatibilidade com jobs processados antes desta mudança.

## Risks / Trade-offs

[Título vazio ou não fornecido] → Mitigation: fallback para comportamento atual; campo não é obrigatório no form (`titulo` ausente é tratado como string vazia).

[Título com caracteres especiais quebrando slug] → Mitigation: função `_slugify` faz normalização Unicode (NFD + remoção de diacríticos) antes de substituir não-alfanuméricos.

[Jobs antigos sem `titulo.txt`] → Mitigation: booklet usa `_extract_title()` como fallback; pipeline de cortes não é re-executado para jobs antigos.

[Nome de arquivo muito longo com slug + slug do corte] → Mitigation: truncar slug do título a 40 caracteres na função `_slugify`.
