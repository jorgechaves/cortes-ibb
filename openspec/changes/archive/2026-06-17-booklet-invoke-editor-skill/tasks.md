## 1. Dependências

- [x] 1.1 Adicionar `anthropic>=0.40` ao `requirements.txt`
- [x] 1.2 Instalar `anthropic` no ambiente virtual: `.venv/bin/pip install anthropic`
- [x] 1.3 Adicionar `ANTHROPIC_API_KEY=` ao `.env.example`

## 2. Reescrever `edit_text()` com fallback em cascata

- [x] 2.1 Definir constante `_SKILL_PATH` no topo de `pipeline/booklet.py`: caminho absoluto para `.agents/skills/editor/SKILL.md` relativo à raiz do projeto (`Path(__file__).resolve().parents[1] / ".agents" / "skills" / "editor" / "SKILL.md"`)
- [x] 2.2 Definir constante `_SKILL_SUFFIX` com as instruções adicionais PT-BR/sermão que são concatenadas ao SKILL.md: instrução de idioma, preservação de citações bíblicas, proibição de resumo, detecção de seções `## Título Breve`, retorno sem comentários
- [x] 2.3 Implementar função `_edit_with_claude(chunk, system_prompt, model, client) -> str` que chama `client.messages.create()` com o system prompt composto e retorna o texto editado
- [x] 2.4 Atualizar `edit_text()` para tentar Anthropic primeiro: verificar `ANTHROPIC_API_KEY` + existência do SKILL.md, construir system prompt composto (`SKILL.md + _SKILL_SUFFIX`), processar chunks via `_edit_with_claude()`, logar "Usando skill /editor via Claude ({model})"
- [x] 2.5 Manter o bloco OpenAI como segundo nível do fallback: se Anthropic não disponível ou SKILL.md ausente, usar OpenAI com o prompt interno atual (comportamento já existente)
- [x] 2.6 Manter o fallback final para texto original se nenhuma API estiver configurada

## 3. Verificação

- [x] 3.1 Confirmar que o módulo importa sem erros: `.venv/bin/python -c "from pipeline import booklet; print('OK')"`
- [x] 3.2 Testar fallback sem ANTHROPIC_API_KEY: rodar com `ANTHROPIC_API_KEY=""` e confirmar que cai no OpenAI ou texto original conforme esperado
- [x] 3.3 Confirmar que as assinaturas públicas `generate_booklet()` e `upload_booklet_to_drive()` não mudaram
