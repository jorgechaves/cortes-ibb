## 1. Pipeline — função run_transcript_only

- [x] 1.1 Definir `TRANSCRIPT_STAGE_WEIGHTS` em `pipeline/__init__.py` com pesos para os estágios `upload`, `probe`, `transcribe` e `drive` somando 100
- [x] 1.2 Criar função `run_transcript_only(source, out_dir, on_event)` em `pipeline/__init__.py` que executa probe + transcribe + drive e retorna dict com `transcript_local_path`, `transcript_drive_url` e `cuts: []`
- [x] 1.3 Garantir que o evento `type: "done"` emitido por `run_transcript_only` tenha `percent: 100.0` e o dict de resultado no campo `data`

## 2. Backend — endpoint /upload com suporte a mode

- [x] 2.1 Adicionar parâmetro `mode: str = Form("cuts")` ao endpoint `/upload` em `app.py`
- [x] 2.2 Criar função `_run_transcript_only` em `app.py` análoga a `_run_pipeline`, que chama `pipeline_mod.run_transcript_only` e publica o resultado no `state.queue`
- [x] 2.3 No endpoint `/upload`, despachar para `_run_pipeline` ou `_run_transcript_only` conforme o valor de `mode`

## 3. Frontend — dois botões de ação e tela de resultado

- [x] 3.1 Em `web/index.html`, substituir o único botão de envio por dois botões lado a lado: "Gerar Cortes" e "Só Transcrição"
- [x] 3.2 Cada botão define a variável JS `currentMode` (`"cuts"` ou `"transcript"`) e inclui o campo `mode` no FormData antes de submeter para `/upload`
- [x] 3.3 Ocultar o checkbox de legenda quando o usuário clicar em "Só Transcrição" (e reexibi-lo se voltar a selecionar "Gerar Cortes")
- [x] 3.4 Na função que trata `type: "done"` no SSE, verificar `currentMode`: se `"transcript"`, renderizar tela de resultado simplificada com link de download local do `transcript.txt` e link do Drive (se disponível), sem seção de cortes
