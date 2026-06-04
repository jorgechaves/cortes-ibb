## Context

O pipeline atual produz 6 MP4 prontos, com seleção semântica que já entende o tema de cada corte (campos `title` e `rationale`). Falta o último passo do fluxo de publicação: o texto do post no feed do Instagram. Hoje o operador escreve à mão, copiando ideias da palestra — caro e propenso a desistir nos posts seguintes.

O selector semântico (`pipeline/semantic_selector.py`) já chama o OpenAI uma vez por job. Esta change reaproveita o mesmo cliente + chave + modelo padrão (`gpt-4o-mini`) para uma chamada extra que recebe os 6 cortes e devolve os 6 pacotes de legenda.

Stakeholders:
- Operador IBB: arrasta o vídeo, espera, recebe MP4 + legendas prontos para colar.
- Equipe de redes sociais: consome o `instagram.md` em uma única visão (revisão) e os `.txt` individuais (copy-paste por post).

## Goals / Non-Goals

**Goals:**
- Gerar, sem interação humana, 6 pacotes de feed (hook + caption + CTA + hashtags) por job.
- Distribuir os textos em formato pronto para uso: Markdown agregado + `.txt` por corte + UI com botão Copiar.
- Ficar dentro do mesmo modelo/SDK (`gpt-4o-mini`) já configurado — sem nova dependência ou chave.
- Não bloquear o pipeline: se a chamada falhar, MP4 + Drive seguem normalmente.

**Non-Goals:**
- Não gerar conteúdo para Twitter/Facebook/YouTube nesta change.
- Não gerar imagem de capa (cards) — só texto.
- Não tentar postar diretamente no Instagram (sem Graph API agora).
- Não traduzir para outros idiomas — só PT-BR.

## Decisions

### Decisão 1: Uma chamada única para os 6 cortes
Mesma estratégia do selector semântico: enviar `[{idx, title, rationale, text}, ...]` para o LLM e receber `[{idx, hook, caption, cta, hashtags}, ...]` em JSON estruturado. Razões:
- Latência total menor (3–5 s vs. 6 chamadas em série).
- O modelo vê o conjunto e evita repetir hashtags ou CTA idênticos.
- Custo único de prompt caching no system prompt.

**Alternativa considerada:** 6 chamadas, uma por corte. Rejeitado — pior latência, custo proporcional e perda de coerência entre posts do mesmo dia.

### Decisão 2: Modelo
`gpt-4o-mini` (mesmo do selector). Tarefa criativa porém formulaica, não requer modelo grande. Permite manter a mesma env var (`OPENAI_MODEL`) com mesmo default.

### Decisão 3: Schema da resposta
Usar `response_format={"type":"json_schema", "strict": true}` com schema que exige:
- `posts`: array de exatamente 6 itens
- Cada item: `idx` (int 1–6), `hook` (string), `caption` (string), `cta` (string), `hashtags` (array de strings, 10–15 itens)

Pós-validação no Python:
- `hook` truncado a 80 chars se passar.
- `hashtags` deduplicadas case-insensitive; cada uma normalizada para começar com `#`; total clampado a 15.
- `caption` mínimo 1 parágrafo (mais que isso é responsabilidade do modelo).

### Decisão 4: Prompt
System prompt fixo (cacheado) com voz e contexto:

```
Você é o gerente de redes sociais de uma igreja batista (IBB). Para cada
corte de palestra, escreve a legenda do post de Instagram com:
- Hook: 1 linha forte (até 80 caracteres), que prende antes do "...mais".
- Caption: 3–6 parágrafos curtos, voz reflexiva, conecta ao cotidiano do
  leitor; sem jargão excessivo, sem versículos inventados.
- CTA: chamada para Salvar, Compartilhar ou Comentar (varia ligeiramente
  entre posts).
- Hashtags: 10–15 em PT-BR, mistura de amplas (#fe, #palavradedeus,
  #devocional) e nichadas (#ibb, #igrejabatista). Sem hashtags genéricas
  de marketing (#instagood, #love, etc).
Responda APENAS com JSON conforme o schema.
```

User message: serializa os 6 cortes em JSON e pede o output.

### Decisão 5: Persistência

`output/<job-id>/instagram.md`:
```markdown
# Instagram — Job <id> (<modo>)

## 1. <title do corte 1>
*<rationale>*

**HOOK:** <hook>

<caption>

_<cta>_

`#tag1 #tag2 ...`

---

## 2. ...
```

`output/<job-id>/corte-01-instagram.txt`:
```
<hook>

<caption>

<cta>

#tag1 #tag2 #tag3 ...
```

Formato `.txt` otimizado para colar direto no Instagram — sem markdown, hashtags numa linha só ao final (Instagram aceita até 30, mas 10–15 dá melhor alcance).

### Decisão 6: Upload de arquivos não-MP4 no Drive
`pipeline/drive.py:upload_all` hoje recebe `[(local_path, name)]` e força `mimeType='video/mp4'`. Refatorar para aceitar `mimeType` opcional por entrada: `[(local_path, name, mime)]`. Backward-compatible se passar tupla de 2.

Padrão de mimeType:
- `.mp4` → `video/mp4`
- `.md`  → `text/markdown`
- `.txt` → `text/plain`

### Decisão 7: Orquestração
Adicionar estágio `instagram` em `pipeline/__init__.py` entre `concat` e `drive`. Pesos atualizados na constante `STAGE_WEIGHTS`:

```python
STAGE_WEIGHTS = {
    "upload": 5,
    "probe": 2,
    "transcribe": 25,
    "select": 3,
    "ass": 5,
    "outro": 5,
    "render": 35,     # 40 → 35
    "concat": 5,
    "instagram": 5,   # novo
    "drive": 10,
}
```

Render perde 5% para abrir espaço — o estágio render continua sendo o mais pesado de qualquer forma (~30–40s vs 3–5s do instagram), então a barra continua representativa.

### Decisão 8: UI
A seção de cada corte ganha um bloco expansível:

```
─────────────────────────────
1. Uma vida para Deus...
   Apresenta a importância da dedicação...
   corte-01-vida-de-dedicacao.mp4 · 72s · [Abrir no Drive]

   ▸ Instagram                              [Copiar]
     HOOK: Você sabe o que Deus...
     CAPTION: ...
     CTA: 👇 Salve este post...
     #fe #palavradedeus #ibb ...
─────────────────────────────
```

Botão **Copiar** usa `navigator.clipboard.writeText()` com o mesmo conteúdo do `.txt`. Confirmação visual ("Copiado!") por 1,5 s.

### Decisão 9: Fallback
Mesma lógica do selector: se `OPENAI_API_KEY` ausente OU 2 falhas seguidas, o estágio loga aviso, marca `instagram_skipped=true` no resultado, segue para `drive`. O `cuts.json` ganha campo `instagram_skipped` + `instagram_skip_reason`. O `report.md` registra.

### Decisão 10: rebuild.py e reupload.py
Esses scripts standalone também devem suportar a geração+upload das legendas para jobs antigos:

- `python3 rebuild.py output/<job> --with-captions` → roda o estágio `instagram` antes do re-upload (gera arquivos se faltarem).
- `python3 reupload.py output/<job> --with-captions` → não regenera MP4, mas se há `instagram.md` e `.txt` na pasta, inclui no upload; se não há e a flag foi passada, gera-os antes.

Sem a flag, comportamento atual preservado.

## Risks / Trade-offs

- **Modelo gera versículos inventados** → spec proíbe explicitamente no system prompt; revisão humana é recomendada antes do post. Mitigação: também avisar no README.
- **Hashtags repetidas entre os 6 posts** → o LLM provavelmente vai gerar bastante overlap; isso na verdade ajuda na consistência de marca. Não vamos forçar diversidade entre posts.
- **Texto fica fora do tom da igreja** → primeira rodada exige revisão; ajustar o system prompt se preciso. Operador pode subir override via env (`IG_SYSTEM_PROMPT_FILE=/path/to/custom.txt`) no futuro (não nesta change).
- **Custo extra** → ~$0.005 por job. Trivial.
- **Falha do estágio impacta UX** → mitigado pelo skip silencioso + banner amarelo.
- **JSON malformado** → retry com `temperature=0` na segunda tentativa (mesma estratégia do selector).
- **Upload Drive demora mais** → 7 arquivos extras (~10–20 KB cada). Latência adicional desprezível.

## Migration Plan

Sem migração de dados — só código novo. Jobs antigos não têm legendas; `rebuild.py --with-captions` (ou `reupload.py --with-captions`) pode gerar e enviar retroativamente.

`cuts.json` ganha 2 campos opcionais (`instagram_skipped`, `instagram_skip_reason`); leitores antigos continuam funcionando porque ignoram campos desconhecidos.

## Open Questions

- Pacote `corte-XX-instagram.txt` ou `corte-XX.md` por corte? Decisão: `.txt` puro (sem markdown) para colar direto no Instagram. O `.md` agregado serve para revisão humana antes de postar.
- Hashtag IBB oficial — existe uma padrão da igreja (`#ibb`, `#ibbpalavra`, etc.)? Default no system prompt: `#ibb`, `#igrejabatista`. Pode ser sobrescrito no futuro via env var ou config.
