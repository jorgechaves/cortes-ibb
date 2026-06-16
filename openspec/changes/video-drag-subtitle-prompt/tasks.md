## 1. Frontend — Modal de escolha de legenda

- [x] 1.1 Adicionar HTML do modal em `web/index.html` (overlay + card com botões "Sim, com legenda" e "Não, sem legenda")
- [x] 1.2 Adicionar CSS do modal (overlay escuro, card centralizado, botões estilizados com variáveis CSS existentes)
- [x] 1.3 Criar variável `pendingFile` para guardar o arquivo antes da escolha
- [x] 1.4 Refatorar `startUpload(file)` para aceitar parâmetro `withSubtitle: boolean`
- [x] 1.5 Interceptar evento `drop` da dropzone para chamar `showSubtitleModal(file)` em vez de `startUpload` diretamente
- [x] 1.6 Interceptar `change` do file picker para chamar `showSubtitleModal(file)`
- [x] 1.7 Implementar `showSubtitleModal(file)`: exibe modal e guarda `pendingFile`
- [x] 1.8 Implementar handlers dos botões do modal: fechar modal e chamar `startUpload(pendingFile, withSubtitle)`
- [x] 1.9 Implementar fechar modal ao clicar no overlay ou pressionar Escape

## 2. Backend — Endpoint /upload

- [x] 2.1 Importar `Form` do FastAPI em `app.py`
- [x] 2.2 Adicionar parâmetro `subtitle: str = Form("true")` na assinatura de `upload()`
- [x] 2.3 Converter `subtitle` para `with_subtitles: bool` (`subtitle.lower() == "true"`)
- [x] 2.4 Repassar `with_subtitles` para `_run_pipeline()` e para `pipeline_mod.run()`

## 3. Pipeline — Condicionar geração de legendas

- [x] 3.1 Adicionar parâmetro `with_subtitles: bool = True` em `pipeline.run()` em `pipeline/__init__.py`
- [x] 3.2 Envolver a etapa `ass` em `if with_subtitles:` — quando `False`, emitir progresso imediato e definir `ass_paths = [None] * len(cuts)`
- [x] 3.3 Repassar `with_subtitles` (ou `ass_path=None`) para `render_cut()` em cada iteração

## 4. Render — Suporte a ass_path=None

- [x] 4.1 Alterar assinatura de `render_cut()` em `pipeline/render.py` para `ass_path: str | None`
- [x] 4.2 Quando `ass_path is None`, construir `filter_complex` apenas com scale + overlay do ícone (sem filtro `subtitles=`)
- [x] 4.3 Quando `ass_path` é fornecido, manter comportamento atual (subtitles + overlay)
