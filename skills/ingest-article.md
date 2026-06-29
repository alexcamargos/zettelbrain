# /ingest-article (Ingestão de artigos da web)

## Objetivo
Processar **apenas** arquivos Markdown em **`raw/articles/`** que representem conteúdo informal da internet (blog, wiki, documentação de produto, newsletter, fórum exportado, notícia, etc.). Estes materiais **não** são tratados como papers formais: não se assume revisão por pares, estrutura IMRaD nem metadados acadêmicos completos. O fluxo prioriza **rastreabilidade** (URL, data de recuperação), **avaliação crítica da fonte** (viés, patrocínio, desatualização, link quebrável) e extração de ideias úteis ao cofre, com linguagem explícita sobre **limites de evidência**.

**Exclusão explícita:** arquivos com `source_kind: youtube_transcript` (armazenados em `raw/youtube/`) devem ser processados por `/ingest-youtube`, não por `/ingest-article`.

## Gatilho
Acionado quando o usuário disser `gemini "Execute a skill /ingest-article no arquivo raw/articles/[nome].md"` ou `/ingest-article raw/articles/[nome].md`.

**Log:** Ao acrescentar entradas em `.state/log.md`, use estritamente o formato definido no `ZETTELBRAIN.md` (seção Convenção do log operacional). No cabeçalho use **`/ingest-article`** e liste todos os arquivos tocados ou criados.

## Fluxo de Execução (Workflow)

### Meta de amplitude
Trate cada ingestão como oportunidade de **reforçar a rede**: literatura web, permanentes novas ou atualizadas, índice, revisões cruzadas com `[[wikilinks]]`. Meta orientadora **três a dez** arquivos quando a base o permitir; se for cofre quase vazio, documente no log a rede mínima alcançada.

### Etapa 1: Leitura e perfil da fonte
1. Leia o arquivo `.md` na íntegra. Extraia do **YAML front matter**, quando existir, campos como `title`, `author`, `authors`, `date`, `published`, `url`, `source`, `site`, `tags`, `canonical_url`. Se o clip vier de ferramenta tipo Web Clipper, preserve o que já estiver estruturado.
2. Classifique mentalmente o **tipo de veículo** (blog corporativo, wiki comunitária, docs oficiais, editorial, post individual, etc.) sem inventar prestígio acadêmico.
3. Registre no corpo da futura nota de literatura, em prosa contínua, uma **avaliação da procedência**: quem publica, conflito de interesses óbvio, se o texto é opinião ou documentação factual, e se há versão mais autoritativa possível (paper, norma, repositório oficial).

### Etapa 2: Citação recuperável (sem confundir com paper)
1. Monte uma **referência bibliográfica** adequada ao tipo de fonte. Para obras online em PT-BR, use o padrão **ABNT** para material eletrônico quando houver URL e data de acesso; quando faltarem dados, documente a lacuna e ofereça a melhor forma **recuperável** (URL principal, nome do site, data de recuperação no formato ISO).
2. **Não** copie tom de artigo científico se a fonte não for isso. Evite expressões como "os autores demonstram estatisticamente" salvo quando o texto original realmente fizer isso.

### Etapa 3: Síntese e conceitos (pausa obrigatória)
Na conversa com o usuário pode usar listas para clareza; isso **não** se aplica ao texto que será gravado em `zettelbrain/`.

1. Apresente ao usuário **nesta conversa** (não no cofre ainda): a referência recuperável, o resumo do argumento central ou utilidade prática, a lista de conceitos ou takeaways candidatos, e um parágrafo curto sobre **confiabilidade e riscos de uso** (marketing, desatualização, escopo limitado).
2. Pergunte explicitamente: "Quais destes tópicos devemos transformar em Notas Permanentes e o que deve ficar apenas na nota de literatura?"
3. Aguarde a resposta antes de gravar notas no `zettelbrain/`.

### Etapa 4: Gravação no cofre
Aplicando as **Regras Globais de Estilo** do `ZETTELBRAIN.md` (título obrigatório no corpo, progressão lógica em prosa contínua sem rótulos literais, sem bullet points no corpo das notas, negrito só para conceitos-chave). Não comprima artificialmente a nota de literatura para caber em poucos parágrafos; quando o artigo for rico, desenvolva a análise em múltiplos parágrafos.

1. **Nota de literatura:** Crie em `zettelbrain/literature/` com `type: literature`, `source_kind: web_article` (ou valor mais específico permitido pelo `ZETTELBRAIN.md`), `source_file` apontando para `raw/articles/...`, campos opcionais `url`, `retrieved_at`, `publisher_kind` quando úteis, `abnt_reference` ou equivalente textual da Etapa 2, e **`confidence` obrigatório** (`high`, `medium` ou `low`) alinhado à avaliação de procedência. O corpo deve começar com `# Título da nota`, deixar claro que a fonte é **informal da web** e manter a estrutura em parágrafos. Cubra em prosa o argumento central, a utilidade prática ou teórica, os conceitos relevantes, exemplos ou evidências usados, riscos de procedência, lacunas e conexões com o cofre.
2. **Notas permanentes:** Somente para os tópicos aprovados, com `sources` apontando para a nota de literatura criada e `# Título da nota` no início do corpo. Antes de concluir cada permanente **nova**, busque notas relacionadas por conceito e adicione wikilinks úteis no texto. Aplique **ligação mínima ao grafo** do `ZETTELBRAIN.md`; se não houver duas notas relacionadas no cofre, registre no log.
3. **Revisão cruzada:** Se alguma nota permanente existente depender de afirmações fortes sustentadas só por esta fonte informal, atualize com cautela ou sinalize tensão epistêmica em prosa.

### Etapa 5: Catalogação e estado
1. Atualize `zettelbrain/index.md` (seção **Fontes web informais** ou equivalente já existente no índice).
2. Atualize o `.state/log.md` com cabeçalho **`/ingest-article`** e **lista explícita** de todos os caminhos relativos criados ou alterados (literatura, permanentes, `index.md`, e notas atualizadas na revisão cruzada).
3. Atualize o `.state/hot.md` como nas demais skills de ingestão.

## Notas de desenho
* **Papers** continuam exclusivamente em `/ingest-paper` e `/ingest-paper-intro` sobre `raw/papers/`.
* Se o usuário apontar um `.md` que na verdade é pré-print ou relatório técnico longo com estrutura de paper, recomende avaliar se o fluxo `/ingest-paper` após conversão para PDF ou outro formato formal não seria mais adequado.
