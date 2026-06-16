## Context

A função `transcribe()` em `pipeline/transcribe.py` já salva `transcript.json` com todas as palavras e seus timestamps. O texto das palavras está disponível imediatamente após a transcrição, sem custo adicional de processamento. O pipeline (`pipeline/__init__.py`) já monta a lista de arquivos para o Drive (`upload_list`) no final do job.

## Goals / Non-Goals

**Goals:**
- Salvar `transcript.txt` com o texto corrido completo na pasta do job, ainda dentro de `transcribe()`
- Incluir `transcript.txt` no upload ao Drive junto com os vídeos e arquivos Instagram
- Incluir `transcript_drive_url` e `transcript_local_path` no objeto de resultado retornado pelo pipeline

**Non-Goals:**
- Formatação com timestamps (esse papel já é do `transcript.json`)
- Segmentação por cortes (o `.txt` é do vídeo original completo)
- Modificar a UI além de exibir o link Drive quando disponível

## Decisions

### 1. Geração do .txt dentro de `transcribe()`, não no `__init__.py`
A função já tem todos os dados (`words`) e o `out_dir`. Gerar o arquivo lá mantém a responsabilidade coesa: `transcribe()` produz todos os artefatos da transcrição. Alternativa considerada: gerar em `__init__.py` com as `words` retornadas — descartada por dispersar responsabilidade.

### 2. Quebra de parágrafo em pausa > 1,5 s
Palavras separadas por mais de 1,5 s de silêncio recebem uma linha em branco antes, tornando o texto legível por blocos temáticos. Alternativa: texto contínuo sem quebras — descartada por dificultar a leitura em transcrições longas.

### 3. `transcript.txt` adicionado ao `upload_list` em `__init__.py`
Segue o mesmo padrão de `instagram.md` e dos `.txt` individuais por corte: verificação de existência antes de adicionar. Nenhuma nova abstração necessária.

## Risks / Trade-offs

- [Transcrição vazia] → `words = []` produz `transcript.txt` vazio; aceitável, não é erro.
- [Falha no Drive] → o erro já é capturado pelo bloco `try/except` existente; `transcript_drive_url` fica `None` no resultado, sem impacto no fluxo.
