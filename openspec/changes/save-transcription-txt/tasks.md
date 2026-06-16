## 1. Transcrição — Gerar transcript.txt

- [x] 1.1 Em `pipeline/transcribe.py`, criar função auxiliar `_words_to_text(words, pause_threshold=1.5)` que une as palavras em texto corrido com linha em branco onde a pausa entre palavras supera o threshold
- [x] 1.2 Após salvar `transcript.json`, salvar `transcript.txt` chamando `_words_to_text(words)` e gravando o resultado em `out_dir/transcript.txt`

## 2. Pipeline — Incluir transcript.txt no upload ao Drive

- [x] 2.1 Em `pipeline/__init__.py`, após montar `upload_list`, adicionar `transcript.txt` à lista se o arquivo existir na pasta do job
- [x] 2.2 Após o upload ao Drive, extrair a URL de `transcript.txt` de `drive_by_name` e armazená-la em `transcript_drive_url`
- [x] 2.3 Incluir `transcript_drive_url` e `transcript_local_path` no dicionário `result` retornado pelo pipeline
- [x] 2.4 Atualizar `_write_report` para incluir o link de transcrição no `report.md` quando disponível

## 3. UI — Exibir link da transcrição nos resultados

- [x] 3.1 Em `web/index.html`, na função `renderResults`, ler `data.transcript_drive_url`
- [x] 3.2 Se `transcript_drive_url` estiver presente, renderizar um botão/link "Transcrição" na seção de resultados (acima dos cards dos cortes), com estilo consistente com os botões Drive existentes
