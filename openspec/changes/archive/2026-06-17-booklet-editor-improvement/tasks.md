## 1. Atualizar SYSTEM prompt em `pipeline/booklet.py`

- [x] 1.1 Substituir a constante `SYSTEM` em `correct_text()` pelo novo prompt de edição profissional PT-BR que inclui: (a) correção ortográfica e gramatical, (b) eliminação de redundâncias, (c) conversão de voz passiva para ativa, (d) fortalecimento de verbos fracos, (e) melhoria de coesão entre parágrafos, (f) variação de estrutura de frases, (g) preservação literal de citações bíblicas e termos teológicos, (h) proibição explícita de resumir/omitir/reordenar, (i) instrução de detecção de seções com `## Título Breve`
- [x] 1.2 Atualizar a mensagem de log de início de edição para: `"Revisando e melhorando o texto em português brasileiro"`
- [x] 1.3 Renomear a função `correct_text()` para `edit_text()` em `pipeline/booklet.py` e atualizar a chamada em `generate_booklet()`
- [x] 1.4 Atualizar a mensagem de stage em `generate_booklet()` de `"Corrigindo português brasileiro"` para `"Revisando e melhorando o texto"`

## 2. Verificação

- [x] 2.1 Confirmar que o módulo importa sem erros após as mudanças: `python -c "from pipeline import booklet; print('OK')"`
- [x] 2.2 Confirmar que a assinatura pública `generate_booklet()` e `upload_booklet_to_drive()` não mudou (sem breaking change na API externa)
