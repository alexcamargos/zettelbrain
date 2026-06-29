# /ingest-youtube (Ingestão de transcrições do YouTube)

## Objetivo
Processar **apenas** arquivos Markdown em `raw/youtube/` gerados pelo ETL de YouTube (`src/ingestion/youtube_etl.py`) com `source_kind: youtube_transcript`. Este fluxo não substitui `/ingest-article`: transcrições de vídeo têm temporalidade, oralidade, risco de erro automático e autoria/publicação próprias, portanto exigem avaliação específica antes de entrar no cofre.

## Gatilho
Acionado quando o usuário disser `gemini "Execute a skill /ingest-youtube no arquivo raw/youtube/[nome].md"` ou `/ingest-youtube raw/youtube/[nome].md`.

**Log:** Ao acrescentar entradas em `.state/log.md`, use estritamente o formato definido no `ZETTELBRAIN.md` (seção Convenção do log operacional). No cabeçalho use **`/ingest-youtube`** e liste todos os arquivos tocados ou criados.

## Fluxo de Execução (Workflow)

### Meta de amplitude
Trate cada transcrição como uma fonte oral informal e potencialmente útil, mas epistemicamente inferior a paper, relatório técnico ou documentação oficial. A meta orientadora continua sendo reforçar a rede com nota de literatura, permanentes aprovadas, índice e revisões cruzadas quando a base permitir; se o cofre estiver vazio ou o vídeo for fraco, documente a limitação no log.

### Etapa 1: Validação do artefato bruto
1. Confirme que o arquivo está em `raw/youtube/`, possui extensão `.md` e traz frontmatter com `source_kind: youtube_transcript`.
2. Extraia do frontmatter `title`, `video_id`, `url`, `published_at` e `retrieved_at`. Se `video_id`, `url` ou `retrieved_at` estiverem ausentes, trate a confiança como no máximo `medium` e registre a lacuna no corpo da nota de literatura.
3. Leia a transcrição integralmente, observando marcas de oralidade, trechos repetitivos, lacunas de contexto, possíveis erros de transcrição automática e afirmações que exigiriam fonte mais autoritativa.

### Etapa 2: Avaliação de procedência e utilidade
Na conversa com o usuário pode usar listas para clareza; isso **não** se aplica ao texto gravado em `zettelbrain/`.

1. Apresente ao usuário um resumo do argumento central do vídeo, a utilidade provável para a pesquisa, os conceitos candidatos a permanentes e uma avaliação curta de confiabilidade.
2. Deixe explícito se a transcrição parece conter opinião, tutorial, relato prático, entrevista, aula, revisão de literatura ou comentário editorial.
3. Pergunte: "Quais destes tópicos devemos transformar em Notas Permanentes e o que deve ficar apenas na nota de literatura da transcrição?"
4. Aguarde a resposta antes de gravar notas no `zettelbrain/`.

### Etapa 3: Gravação no cofre
Aplicando as **Regras Globais de Estilo** do `ZETTELBRAIN.md`, sem bullet points no corpo das notas e com título obrigatório após o YAML. Não comprima artificialmente a nota de literatura para caber em poucos parágrafos; use tantos parágrafos de prosa contínua quantos forem necessários para cobrir a transcrição com suficiência.

1. **Nota de literatura:** Crie em `zettelbrain/literature/` com `type: literature`, `source_kind: youtube_transcript`, `source_file` apontando para `raw/youtube/...`, `video_id`, `url`, `retrieved_at`, `published_at` quando disponível, `publisher_kind: youtube_channel`, `abnt_reference` em melhor forma recuperável para vídeo online e `confidence` obrigatório (`high`, `medium` ou `low`). O corpo deve começar com `# Título da nota`, explicar que a fonte é uma transcrição de vídeo e registrar limitações de evidência. Desenvolva a nota em prosa contínua, cobrindo argumento central, percurso explicativo, exemplos usados no vídeo, conceitos candidatos, riscos de oralidade ou transcrição e conexões úteis com o cofre.
2. **Notas permanentes:** Somente para tópicos aprovados pelo usuário. Use `sources` apontando para a nota de literatura criada e conecte com `[[wikilinks]]` para notas relacionadas quando existirem candidatas claras.
3. **Revisão cruzada:** Se a transcrição reforçar ou tensionar notas existentes, atualize com cautela e deixe claro que a evidência vem de fonte oral informal.

### Etapa 4: Catalogação e estado
1. Atualize `zettelbrain/index.md` na seção **Transcrições do YouTube**. Se a seção não existir, crie-a próxima de **Fontes web informais**.
2. Atualize `.state/log.md` com cabeçalho **`/ingest-youtube`** e lista explícita de todos os caminhos relativos criados, alterados e lidos em profundidade.
3. Atualize `.state/hot.md` com o foco da sessão quando a transcrição mudar a direção imediata da pesquisa.

## Notas de desenho
* Use `/ingest-article` para blogs, documentação, notícias, wikis e outros textos web não derivados do ETL de YouTube.
* Use `/ingest-paper` para PDFs e documentos formais densos.
* Se a transcrição referenciar um paper, norma ou relatório técnico, trate isso como pista para ingestão futura da fonte primária, não como substituto da fonte primária.
