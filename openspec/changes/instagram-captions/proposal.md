## Why

Hoje o app entrega 6 MP4 prontos para postar, mas o operador ainda precisa escrever, manualmente, 6 legendas de Instagram para os posts. Esse é o trabalho mais repetitivo e mais demorado depois do upload. Reaproveitar a transcrição + título + rationale que o pipeline já gera permite produzir as legendas com a mesma chamada que já entendeu o tema do corte — sem trabalho extra para o operador.

## What Changes

- Adicionar um estágio novo no pipeline: `instagram` (entre `concat` e `drive`).
- Para cada corte, gerar um pacote de feed contendo:
  - **Hook** — 1 linha forte (≤ 80 caracteres) que prende antes do "...mais" do Instagram.
  - **Caption** — 3–6 parágrafos curtos em PT-BR, voz reflexiva/devocional alinhada com a IBB.
  - **CTA** — chamada padronizada para Salvar / Comentar / Compartilhar.
  - **Hashtags** — 10–15 mistas (amplas como `#fe`, `#palavradedeus` + nichadas como `#ibb`, `#devocional`).
- Persistir os textos em:
  - `output/<job-id>/instagram.md` — arquivo único com os 6 posts (uso humano).
  - `output/<job-id>/corte-XX-instagram.txt` — um arquivo por corte (uso programático / copiar-colar).
- Subir os mesmos arquivos para a subpasta do Drive `videos-ibb/[YYYY-MM-DD]`, ao lado dos MP4.
- Exibir as legendas na UI no estado `done` com botão **Copiar** por corte.
- Mesmo selector semântico atual (OpenAI `gpt-4o-mini`) é reutilizado para a geração: uma única chamada por job que recebe todos os 6 cortes (título + rationale + texto transcrito) e devolve os 6 pacotes em JSON.
- Fallback: se `OPENAI_API_KEY` ausente OU a chamada falha duas vezes, o estágio é pulado com aviso; o restante do pipeline (cortes + Drive) continua normal.

## Capabilities

### New Capabilities
- `instagram-captions`: geração automática de textos de feed (hook + caption + CTA + hashtags) para cada corte, persistidos localmente e no Drive.

### Modified Capabilities
- `video-cuts-app`: barra de progresso ganha um estágio novo `instagram` (peso ~5%); UI exibe os textos no estado de resultado com botão Copiar.
- `video-cuts-ibb`: o upload Drive passa a incluir os arquivos de legenda (`instagram.md` + `corte-XX-instagram.txt`), além dos MP4.

## Impact

- Novo módulo: `pipeline/instagram.py`.
- Mudanças em: `pipeline/__init__.py` (orquestração), `pipeline/drive.py` (aceita lista de arquivos arbitrários, não só MP4), `app.py` (encaminha legendas para a UI), `web/index.html` (renderiza posts + botão Copiar).
- Custo: ~1 chamada OpenAI adicional por job (~3K in / ~2K out) — centavos.
- Latência adicional: ~3–5 s no estágio novo. Cabe no peso da barra.
- `rebuild.py` e `reupload.py` ganham flag `--with-captions` opcional para regerar/reenviar incluindo as legendas.
- Reaproveita a chave OpenAI já configurada (`.env`).
