## 1. Módulo de geração (`pipeline/instagram.py`)

- [x] 1.1 Criar `pipeline/instagram.py` com `def generate(cuts, on_event, *, model=None) -> list[InstagramPost] | None`
- [x] 1.2 Reusar cliente `openai.OpenAI()` lazy; ler `OPENAI_API_KEY` e `OPENAI_MODEL` do ambiente (defaults idênticos ao `semantic_selector`)
- [x] 1.3 System prompt fixo (com prompt caching) descrevendo voz da IBB, formato, restrições (não inventar versículos, sem hashtags genéricas de marketing)
- [x] 1.4 User message: serializa os 6 cortes com `idx`, `title`, `rationale`, `text` (texto transcrito do trecho)
- [x] 1.5 `response_format={"type":"json_schema", "strict": true}` exigindo `posts[6]` com `idx`, `hook`, `caption`, `cta`, `hashtags[]`
- [x] 1.6 Validação pós-resposta: 6 entradas únicas, `hook` truncado a 80 chars, `hashtags` deduplicadas (case-insensitive) e clampadas a 15, cada hashtag começa com `#`
- [x] 1.7 Retry uma vez com `temperature=0` em erro de JSON ou validação
- [x] 1.8 Emitir eventos `progress` (0.1, 0.7, 1.0) e `log` com uso (`prompt_tokens`/`completion_tokens`)
- [x] 1.9 Em falha definitiva, retornar `None` (não levanta) para o orquestrador decidir
- [x] 1.10 Teste unitário com fixture de 6 cortes sintéticos

## 2. Persistência local

- [x] 2.1 Em `pipeline/instagram.py`, função `write_files(posts, cuts, out_dir)` que cria `instagram.md` e `corte-XX-instagram.txt`
- [x] 2.2 `instagram.md` agrega todos os 6 com headings, hook em negrito, caption em prosa, CTA em itálico, hashtags em code block
- [x] 2.3 `corte-XX-instagram.txt` formato copy-paste: hook + linha em branco + caption + linha em branco + CTA + linha em branco + hashtags numa linha
- [x] 2.4 Codificação UTF-8 em ambos

## 3. Orquestração (`pipeline/__init__.py`)

- [x] 3.1 Adicionar `"instagram": 5` em `STAGE_WEIGHTS` e diminuir `render` de 40 para 35
- [x] 3.2 Inserir estágio `instagram` entre `concat` e `drive`: chama `instagram.generate(cuts, emit)` e, se sucesso, `instagram.write_files(...)`
- [x] 3.3 Marcar `instagram_skipped=true` + `instagram_skip_reason` no resultado quando `generate` retorna None ou `OPENAI_API_KEY` ausente
- [x] 3.4 Atualizar `cuts.json` com os 2 novos campos
- [x] 3.5 Atualizar `report.md` para incluir, por corte, hook + caption + CTA + hashtags (quando disponível)
- [x] 3.6 No upload Drive, montar lista incluindo `instagram.md` e os 6 `corte-XX-instagram.txt` quando não pulado

## 4. Refator de `pipeline/drive.py` para suportar mimeTypes

- [x] 4.1 `upload_file(...)` aceita parâmetro `mime: str` opcional (default `video/mp4`)
- [x] 4.2 `upload_all(...)` aceita lista `[(local_path, name, mime?)]` (tupla de 2 ou 3); inferir mime a partir da extensão se omitido (`.mp4`→`video/mp4`, `.md`→`text/markdown`, `.txt`→`text/plain`)
- [x] 4.3 Atualizar callers (`pipeline/__init__.py`, `rebuild.py`, `reupload.py`) sem regressão dos jobs sem legendas

## 5. App / UI

- [x] 5.1 `app.py` continua transparente — o evento `done` já carrega `result.cuts` e o campo `instagram_skipped`; nada novo no transport
- [x] 5.2 `web/index.html`: para cada corte com `instagram` no payload, renderizar bloco expansível "Instagram" com hook/caption/CTA/hashtags
- [x] 5.3 Botão **Copiar** por corte usa `navigator.clipboard.writeText()` com texto formatado (igual ao `.txt`)
- [x] 5.4 Feedback visual: troca o label para "Copiado!" por 1,5 s
- [x] 5.5 Banner amarelo quando `instagram_skipped=true` com motivo legível
- [x] 5.6 Estilo CSS: bloco com fundo levemente diferente para destacar a área de legenda

## 6. Scripts standalone (`rebuild.py` e `reupload.py`)

- [x] 6.1 `rebuild.py`: argumento opcional `--with-captions` que dispara `instagram.generate` + `write_files` antes do upload
- [x] 6.2 `reupload.py`: argumento opcional `--with-captions`; se a flag passar e os arquivos não existem, gera-os; inclui no upload list
- [x] 6.3 Sem a flag, comportamento atual preservado (não gera, não envia legendas)
- [x] 6.4 Atualizar docstrings dos dois scripts

## 7. Documentação

- [x] 7.1 Atualizar `README.md` com nova seção "Legendas para Instagram" explicando: o que é gerado, onde fica, como copiar, como pular (`DISABLE_INSTAGRAM=1` se quisermos a env)
- [x] 7.2 Mencionar o aviso de "revisão humana antes de postar" (modelo pode imaginar versículos)
- [x] 7.3 Documentar `rebuild.py --with-captions` e `reupload.py --with-captions`

## 8. Validação end-to-end

- [ ] 8.1 Rodar novo job pelo app: confirmar que aparece estágio `instagram` na barra
- [ ] 8.2 Conferir que `instagram.md` e os 6 `corte-XX-instagram.txt` existem em `output/<job-id>/`
- [ ] 8.3 Conferir que a subpasta no Drive recebe 13 arquivos (6 MP4 + 1 .md + 6 .txt)
- [ ] 8.4 Conferir que a UI mostra hook/caption/CTA/hashtags por corte e o botão **Copiar** funciona
- [ ] 8.5 Testar fallback: rodar com `OPENAI_API_KEY` removida → estágio é pulado, banner aparece
- [ ] 8.6 Testar `rebuild.py --with-captions output/<job-id>` em um job antigo: legendas geradas + reupload com todos os arquivos

## 9. Encerramento

- [ ] 9.1 Marcar a change como pronta para `/opsx:archive` após validação end-to-end aprovada
