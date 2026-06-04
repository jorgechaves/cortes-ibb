# Cortes IBB

App local em Python 3 que, a partir de um vídeo arrastado para o navegador, gera 6 cortes editados (~60 s cada) com legendas, ícone, cartão final com logo e faz upload para a pasta `videos-ibb` no Google Drive.

## Instalação (uma vez)

1. **ffmpeg** no PATH:

   ```bash
   brew install ffmpeg
   ```

2. **Dependências Python** (recomenda-se `venv`):

   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Credenciais Google Drive** (uma vez):

   - Acesse <https://console.cloud.google.com/>, crie um projeto, ative a *Google Drive API*.
   - Em **APIs & Services → Credentials → Create Credentials → OAuth client ID** escolha *Desktop app*.
   - Baixe o JSON e salve como `~/.config/cortes-ibb/credentials.json`.
   - Na primeira execução o app abrirá o navegador para consentimento e gravará `~/.config/cortes-ibb/token.json`.

4. **Chave OpenAI** (opcional, para seleção semântica dos cortes):

   ```bash
   export OPENAI_API_KEY="sk-..."
   ```

   Modelo padrão: `gpt-4o-mini` (o mais simples e barato com `response_format=json_schema`). Custo na casa de centavos por job. Sem a chave o app cai para uma heurística estrita (pausa + pontuação) e marca os cortes como `selection_mode='heuristic'`. Veja [Como a seleção funciona](#como-a-seleção-funciona).

5. **Fonte** Antique Olive (já instalada no sistema do operador). Se ausente, o app usa `Arial Black` como fallback.

## Uso

```bash
python3 app.py
```

O app:
- escolhe uma porta livre em `7860–7870`;
- abre o navegador em `http://127.0.0.1:<porta>/`;
- mostra a drop zone — arraste o `.mp4` para começar.

Acompanhe a barra de progresso até 100%. Ao terminar, a UI lista os 6 cortes com título, justificativa, duração e link para o Drive.

## Variáveis de ambiente

| Variável | Default | Descrição |
|---|---|---|
| `OPENAI_API_KEY` | — | Habilita seleção semântica (OpenAI). Sem ela, fallback heurístico. |
| `OPENAI_MODEL` | `gpt-4o-mini` | Modelo OpenAI para selecionar os 6 trechos. |
| `DISABLE_SEMANTIC_SELECTION` | — | Se setada (`=1`), força fallback heurístico mesmo com `OPENAI_API_KEY`. |
| `DISABLE_INSTAGRAM` | — | Se setada (`=1`), pula a geração das legendas de Instagram. |
| `WHISPER_MODEL` | `small` | Modelo faster-whisper: `tiny`, `base`, `small`, `medium`, `large-v3`. |
| `CORTES_FONT` | `Antique Olive Std` | Família da fonte da legenda. |
| `CORTES_FONT_SIZE` | `28` | Override do tamanho da legenda em pt. |

## Como a seleção funciona

O backend gera entre 12 e 20 janelas-candidato de 50–75 s ancoradas em pausas longas (>700 ms) e pontuação final (`.`, `?`, `!`). Em seguida:

- **Modo semântico** (default quando `OPENAI_API_KEY` está definida): o `gpt-4o-mini` recebe todos os candidatos em uma única chamada (com `response_format=json_schema` para garantir saída válida) e retorna 6 escolhas com `title` e `rationale`, otimizando por ideia completa, abertura clara, fechamento conclusivo, valor isolado e diversidade.
- **Modo heurístico** (fallback): filtra para fronteiras com pontuação final e distribui 6 trechos uniformemente. Sem `rationale`.

O modo usado fica registrado em `output/<job-id>/cuts.json` e aparece como banner na UI quando é o heurístico.

## Legendas para Instagram

Após render+concat, o pipeline chama `gpt-4o-mini` uma vez com os 6 cortes (`title` + `rationale` + transcrição) e recebe os 6 pacotes de post de feed:

- **Hook** — 1 linha forte (≤ 80 chars), prende antes do "...mais".
- **Caption** — 3–6 parágrafos curtos, voz reflexiva da IBB.
- **CTA** — Salvar / Comentar / Compartilhar.
- **Hashtags** — 10–15 PT-BR mistas (`#fe`, `#palavradedeus`, `#ibb`, ...).

Saída:

- `output/<job-id>/instagram.md` — agregado em Markdown para revisão humana.
- `output/<job-id>/corte-XX-instagram.txt` — 1 arquivo por corte, formato copy-paste.
- Subpasta `videos-ibb/[YYYY-MM-DD]` do Drive recebe ambos junto dos MP4.
- UI mostra hook/caption/CTA/hashtags por corte com botão **Copiar** que coloca o texto formatado no clipboard.

**Reveja antes de postar.** O modelo é instruído a não inventar versículos, mas é prudente conferir o texto e ajustar tom/citações se necessário.

Para pular a geração: `DISABLE_INSTAGRAM=1`. Para gerar/reenviar em um job antigo:

```bash
python3 rebuild.py output/<job-id> --with-captions      # regenera MP4 + legendas + reupload
python3 reupload.py output/<job-id> --with-captions     # mantém MP4, gera legendas se faltam, reupload
```

## Saídas

Para cada job (timestamp + slug), o app cria:

```
output/<job-id>/
├── source.mp4                       # cópia do vídeo arrastado
├── transcript.json                  # transcrição com word-level timestamps
├── cuts.json                        # 6 cortes + metadados + posts Instagram
├── corte-01-<slug>.mp4              # ... corte-06-<slug>.mp4
├── instagram.md                     # agregado de revisão
├── corte-01-instagram.txt           # ... corte-06-instagram.txt
├── drive-ids.json                   # IDs do Drive após upload
└── report.md            # resumo legível
```

## Limitações conhecidas

- 1 job por vez (uploads concorrentes recebem HTTP 409).
- Só Mac/Linux (depende de `fc-list`, `~/.config/`).
- Primeira execução baixa o modelo Whisper (`small` ≈ 500 MB).
