## 1. selector.py — 10 bins e heurístico

- [x] 1.1 Em `gather_candidates`, alterar distribuição de bins de 6 para 10 e recalcular `per_bin = ceil(50/10) = 5`
- [x] 1.2 Renomear `pick_six_heuristic` para `pick_n_heuristic` com parâmetro `n=10`
- [x] 1.3 Atualizar todas as referências a `pick_six_heuristic` em `pipeline/__init__.py`

## 2. semantic_selector.py — schema e greedy target

- [x] 2.1 Atualizar JSON schema: `minItems: 12 → 18`, `maxItems: 18 → 24`
- [x] 2.2 Atualizar `_build_user_message`: `n = min(18, ...)` → `n = min(24, ...)`; ajustar texto do prompt de "6" para "10"
- [x] 2.3 Atualizar `_greedy_nonoverlap`: argumento default `n=6` → `n=10`
- [x] 2.4 Atualizar SYSTEM_PROMPT: referências a "6" → "10" (candidatos e diversidade)

## 3. instagram.py — schema e validação

- [x] 3.1 Atualizar JSON schema: `minItems: 6 → 10`, `maxItems: 6 → 10`
- [x] 3.2 Atualizar `_validate`: checar `len(posts) != 10` em vez de `!= 6`
- [x] 3.3 Atualizar `generate`: checar `len(cuts) != 10` em vez de `!= 6`

## 4. pipeline/__init__.py — fallback e guards

- [x] 4.1 Atualizar guard de fallback de duração: comentário `< 6 candidatos` → `< 10 candidatos`
- [x] 4.2 Atualizar a chamada ao seletor heurístico para usar `pick_n_heuristic`
- [x] 4.3 Atualizar comentário/log do erro quando `len(cuts) < 10`

## 5. drive.py — nome da pasta = job_id

- [x] 5.1 Em `upload_all`, substituir `subfolder_name = f"[{datetime.now().strftime('%Y-%m-%d')}]"` por `subfolder_name = Path(out_dir).name`
- [x] 5.2 Remover import de `datetime` se não for mais usado em outro lugar no arquivo
