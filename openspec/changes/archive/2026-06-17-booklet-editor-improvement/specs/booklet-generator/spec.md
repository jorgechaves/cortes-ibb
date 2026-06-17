## MODIFIED Requirements

### Requirement: Correção de português brasileiro com detecção opcional de seções
O sistema SHALL enviar o transcript ao OpenAI em chunks de até 1.500 palavras aplicando edição profissional completa em português brasileiro, seguindo os princípios da skill `/editor`: correção ortográfica e gramatical, eliminação de redundâncias, conversão de voz passiva para ativa, fortalecimento de verbos fracos, melhoria de coesão entre parágrafos e variação de estrutura de frases. O prompt SHALL instruir o modelo a identificar transições temáticas naturais no sermão e a prefixar o primeiro parágrafo de cada nova seção com `## Título Breve` (máximo 5 palavras extraídas do conteúdo que se segue). O sistema SHALL preservar literalmente citações bíblicas e termos teológicos. O sistema NÃO DEVE resumir, omitir, reordenar ou alterar o conteúdo. Se a edição falhar, o sistema SHALL usar o texto original sem modificação.

#### Scenario: Texto retornado com edição profissional completa
- **WHEN** OPENAI_API_KEY está configurada e o sermão tem redundâncias, voz passiva ou verbos fracos
- **THEN** o texto resultante tem clareza melhorada, redundâncias eliminadas e voz ativa, mantendo todo o conteúdo original

#### Scenario: Citações bíblicas preservadas literalmente
- **WHEN** o transcript contém citações de versículos bíblicos (ex: "Portanto agora nenhuma condenação há...")
- **THEN** a citação aparece no livreto sem alteração, mesmo que o editor melhore o texto ao redor

#### Scenario: Texto retornado com seções identificadas
- **WHEN** o OpenAI identifica transições temáticas e insere marcadores `##`
- **THEN** o PDF renderiza esses blocos como títulos de seção teal com linha dourada

#### Scenario: Fallback sem API key
- **WHEN** OPENAI_API_KEY não está configurada
- **THEN** o texto original é usado sem correção nem marcadores de seção, e o log exibe "OPENAI_API_KEY ausente — usando texto original"

#### Scenario: Fallback por erro de chunk
- **WHEN** a chamada à API OpenAI falha para um chunk específico
- **THEN** o chunk original é inserido sem edição, o processamento continua com os chunks seguintes, e o log registra o erro do chunk

#### Scenario: Mensagem de progresso no log
- **WHEN** a edição começa
- **THEN** o log exibe "Revisando e melhorando o texto em português brasileiro" (não a mensagem anterior "Corrigindo português brasileiro")
