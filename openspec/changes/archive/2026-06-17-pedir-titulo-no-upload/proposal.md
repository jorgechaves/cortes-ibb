## Why

Hoje, ao arrastar um vídeo para processar, os cortes gerados recebem nomes genéricos baseados apenas no `job_id` e os livretos gerados não têm título personalizado na capa. Pedir o título do sermão no momento do upload resolve isso de forma direta, sem exigir etapas extras após o processamento.

## What Changes

- O modal de opções de processamento (atualmente só pergunta sobre legendas) passa a incluir um campo de texto para o título do sermão.
- O título é enviado junto com o vídeo no `POST /upload` e armazenado no `job_dir` como `titulo.txt`.
- O pipeline de cortes usa o título como prefixo/sufixo nos nomes dos arquivos de saída.
- O gerador de livreto lê o `titulo.txt` do `job_dir` em vez de extrair o título do transcript.
- O nome do arquivo `livreto.pdf` gerado incorpora o título do sermão.

## Capabilities

### New Capabilities

- `sermon-title-input`: Captura do título do sermão na interface web no momento do upload, com persistência no `job_dir`.

### Modified Capabilities

- `booklet-generator`: O livreto passa a usar o título persistido em `titulo.txt` (em vez de extrair do transcript), e o nome do arquivo PDF gerado incorpora o título do sermão.
- `drive-upload`: Os cortes e o livreto enviados ao Drive usam nomes que incorporam o título do sermão.

## Impact

- `web/index.html`: Modal de processamento ganha campo de texto para o título.
- `app.py`: Rota `/upload` recebe novo campo `titulo` via form; salva `titulo.txt` no `job_dir`.
- `pipeline/`: Lógica de nomeação dos cortes usa o título ao nomear arquivos de saída.
- `pipeline/booklet.py`: Leitura do título via `titulo.txt` em vez de extração do transcript.
- Nenhuma quebra de compatibilidade na API pública — o campo `titulo` é opcional com fallback para string vazia.
