## 1. Backend — Persistência do título

- [x] 1.1 Adicionar parâmetro `titulo: str = Form("")` à rota `POST /upload` em `app.py`
- [x] 1.2 Após criar `job_dir`, salvar `titulo.strip()` em `output/{job_id}/titulo.txt` se não vazio

## 2. Pipeline — Função _slugify e prefixo nos cortes

- [x] 2.1 Implementar `_slugify(text: str, max_len: int = 40) -> str` em `pipeline/__init__.py` (NFD + remoção de diacríticos, lowercase, non-alphanum → `-`, hifens consecutivos colapsados, truncado a `max_len`)
- [x] 2.2 No início de `run()` em `pipeline/__init__.py`, ler `titulo.txt` do `job_dir` e calcular `titulo_slug` (vazio se arquivo ausente)
- [x] 2.3 Ao nomear os arquivos finais dos cortes (linha ~177), prefixar com `{titulo_slug}-` quando `titulo_slug` não for vazio: `f"{titulo_slug}-corte-{c.idx:02d}-{c.slug}.mp4"` → senão manter nome atual

## 3. Booklet — Leitura do título e nome do PDF

- [x] 3.1 Em `generate_booklet()` em `pipeline/booklet.py`, ler `titulo.txt` do `job_dir`; usar valor como `title` se não vazio, senão chamar `_extract_title()` como fallback
- [x] 3.2 Importar / reutilizar `_slugify` de `pipeline/__init__.py` no booklet (ou mover para `pipeline/utils.py` se necessário)
- [x] 3.3 Em `app.py`, calcular `out_path` do livreto como `livreto-{titulo_slug}.pdf` quando `titulo.txt` existir; senão `livreto.pdf`

## 4. Frontend — Campo de título no modal

- [x] 4.1 Em `web/index.html`, adicionar `<input type="text" id="titulo-input" placeholder="Título do sermão (opcional)">` dentro de `#subtitle-overlay` acima dos botões
- [x] 4.2 Adicionar estilo CSS para o campo de título (consistente com o design atual do modal)
- [x] 4.3 Em `startUpload()`, ler `document.getElementById('titulo-input').value` e incluir no FormData como `form.append('titulo', tituloValue)`
- [x] 4.4 Ao fechar/resetar o modal (após upload ou cancelamento), limpar o campo `titulo-input`
