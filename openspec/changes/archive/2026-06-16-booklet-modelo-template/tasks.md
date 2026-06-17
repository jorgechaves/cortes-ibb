## 1. Constantes e paleta de cores

- [x] 1.1 Definir constantes de cor no topo de `pipeline/booklet.py`: `NAVY = (0.086, 0.141, 0.227)`, `GOLD = (0.769, 0.588, 0.227)`, `TEAL = (0.290, 0.565, 0.643)`, `GRAY_HEADER = (0.533, 0.533, 0.533)`, `BODY_TEXT = (0.102, 0.102, 0.102)`
- [x] 1.2 Definir constantes de layout: `BAR_H = 28` (altura das barras douradas em pontos), `VBAR_W = 18` (largura da barra vertical), `ICON_SMALL = 30` (ícone da capa), `ICON_BIG = 100` (ícone da contracapa), `CONTENT_LEFT = 36` (margem esquerda do conteúdo na capa)

## 2. Função de capa (cover page)

- [x] 2.1 Reescrever callback `on_cover(c, doc)`: preencher fundo com `NAVY`, desenhar barra dourada horizontal no topo (`rect(0, page_h - BAR_H, page_w, BAR_H)`), no rodapé (`rect(0, 0, page_w, BAR_H)`), e barra vertical esquerda (`rect(0, BAR_H, VBAR_W, page_h - 2*BAR_H)`)
- [x] 2.2 Adicionar `icone.png` no topo-esquerdo da capa: posição `(CONTENT_LEFT, page_h - BAR_H - ICON_SMALL - 10)`, tamanho `ICON_SMALL × ICON_SMALL`
- [x] 2.3 Adicionar texto "IBB — Igreja Batista Belém" em `GOLD`, fonte `Helvetica` 8pt, posição `(CONTENT_LEFT + ICON_SMALL + 6, page_h - BAR_H - ICON_SMALL + 10)`
- [x] 2.4 Renderizar título do sermão em `Helvetica-Bold` 36pt branca, com word-wrap na largura `page_w - CONTENT_LEFT - margin`, a partir de `y ≈ page_h * 0.48`
- [x] 2.5 Desenhar linha dourada sob o título: `rect(CONTENT_LEFT, title_bottom_y - 10, page_w - CONTENT_LEFT - margin, 1.5)` em `GOLD`
- [x] 2.6 Adicionar texto "Pr. Carlos Chaves" em `Helvetica` 12pt branca na posição `(CONTENT_LEFT, BAR_H + 16)`

## 3. Função de contracapa (back cover page)

- [x] 3.1 Reescrever callback `on_back_cover(c, doc)`: fundo `NAVY`, mesmas barras douradas horizontais e vertical da capa
- [x] 3.2 Centralizar `icone.png` na contracapa: tamanho `ICON_BIG × ICON_BIG`, posição `((page_w - ICON_BIG) / 2, (page_h - ICON_BIG) / 2)`

## 4. Função de páginas de conteúdo (content pages)

- [x] 4.1 Reescrever callback `on_content(c, doc)`: desenhar texto de cabeçalho `{título} I {referência}` em `Helvetica` 8.5pt cor `GRAY_HEADER`, posicionado em `(margin, page_h - margin + 10)`
- [x] 4.2 Desenhar linha dourada sob o cabeçalho: `rect(margin, page_h - margin + 2, page_w - 2*margin, 0.75)` em `GOLD`
- [x] 4.3 Desenhar número de página em `Helvetica` 9pt `GRAY_HEADER` centralizado em `(page_w/2, margin - 15)`, usando `doc.page - 1` (subtrai a capa)

## 5. Estilos de parágrafo e seção

- [x] 5.1 Definir `body_style` com `fontName="Times-Roman"`, `fontSize=11`, `leading=14.3`, `alignment=TA_JUSTIFY`, `textColor=BODY_TEXT` convertido para `HexColor`, `spaceAfter=8`
- [x] 5.2 Definir `section_style` com `fontName="Helvetica-Bold"`, `fontSize=15`, `textColor=HexColor("#4a90a4")`, `spaceBefore=14`, `spaceAfter=4`
- [x] 5.3 Definir flowable `SectionRule` (subclasse de `Flowable`) que desenha uma linha horizontal de 0.75pt em `GOLD` na largura total da frame, usada após cada título de seção

## 6. Parser do texto e construção do story

- [x] 6.1 Atualizar `_parse_story(text, body_style, section_style)` para dividir o texto em `\n\n` e, para cada bloco: se começa com `## `, criar `Paragraph(heading, section_style)` + `SectionRule()`, caso contrário criar `Paragraph(body, body_style)`
- [x] 6.2 Atualizar `generate_booklet()` para extrair `title` e usar `title.upper()` ou title-case no cabeçalho do content page; armazenar `title` e `ref` como variáveis de closure acessíveis pelo callback `on_content`

## 7. Atualização do prompt de correção OpenAI

- [x] 7.1 Atualizar a constante `SYSTEM` em `correct_text()` para incluir instrução de detecção de seções: ao identificar uma transição temática natural no sermão, prefixar o primeiro parágrafo da nova seção com `## Título Breve` (máx 5 palavras do próprio texto). Se não houver seções claras, retornar sem marcadores

## 8. Frame de conteúdo ajustado

- [x] 8.1 Ajustar `content_frame` em `generate_booklet()`: top = `page_h - margin - 20` (abaixo do cabeçalho + linha dourada), bottom = `margin + 10` (acima do número de página), usando a fórmula `Frame(margin, margin + 10, page_w - 2*margin, page_h - 2*margin - 30)`

## 9. Teste visual

- [x] 9.1 Gerar PDF de teste com `output/20260616-125521-0cdc/transcript.txt` usando o novo código e abrir para comparação visual com `modelo_livreto.pdf`
- [x] 9.2 Verificar capa: fundo azul-marinho, barras douradas, ícone, título, linha, autor
- [x] 9.3 Verificar páginas de conteúdo: cabeçalho cinza + linha dourada, corpo justificado, número de página
- [x] 9.4 Verificar contracapa: fundo azul-marinho, barras douradas, ícone centralizado
