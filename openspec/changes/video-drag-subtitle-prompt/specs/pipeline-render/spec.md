## ADDED Requirements

### Requirement: Pipeline condiciona geração de legendas à flag with_subtitles
A função `pipeline.run()` SHALL aceitar o parâmetro `with_subtitles: bool` (default `True`). Quando `with_subtitles=False`, o pipeline SHALL pular a geração de arquivos ASS e SHALL passar `ass_path=None` para `render_cut()`. Quando `with_subtitles=True`, o comportamento SHALL ser idêntico ao atual.

#### Scenario: Pipeline executado com with_subtitles=True
- **WHEN** `pipeline.run()` é chamado com `with_subtitles=True`
- **THEN** a etapa `ass` gera arquivos `.ass` para cada corte
- **THEN** `render_cut()` recebe o caminho do arquivo ASS e queima a legenda no vídeo

#### Scenario: Pipeline executado com with_subtitles=False
- **WHEN** `pipeline.run()` é chamado com `with_subtitles=False`
- **THEN** a etapa `ass` é pulada (nenhum arquivo `.ass` é gerado)
- **THEN** `render_cut()` é chamado com `ass_path=None`
- **THEN** o vídeo renderizado contém apenas o overlay do ícone, sem legendas queimadas

### Requirement: render_cut suporta modo sem legenda
A função `render_cut()` em `pipeline/render.py` SHALL aceitar `ass_path: str | None`. Quando `ass_path=None`, SHALL construir um `filter_complex` sem o filtro `subtitles=`, mantendo apenas o scale e overlay do ícone.

#### Scenario: render_cut com ass_path fornecido
- **WHEN** `render_cut()` é chamado com `ass_path` apontando para um arquivo `.ass` válido
- **THEN** o FFmpeg usa o filtro `subtitles=filename='...'` e queima a legenda no vídeo

#### Scenario: render_cut com ass_path=None
- **WHEN** `render_cut()` é chamado com `ass_path=None`
- **THEN** o FFmpeg usa um `filter_complex` sem `subtitles=`, produzindo vídeo sem legenda queimada
- **THEN** o overlay do ícone é aplicado normalmente
