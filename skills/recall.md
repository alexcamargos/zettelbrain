# /recall (Busca e Validação de Contexto)

## Objetivo
Minerar o diretório `zettelbrain/` para recuperar informações precisas sobre um tópico, sintetizar o conhecimento acumulado, identificar lacunas relevantes no cofre e, quando necessário, criar nota permanente nova para fechar a lacuna antes de iniciar materiais definitivos ou análises avançadas.

## Gatilho
Acionado quando o usuário disser `gemini "Execute a skill /recall sobre [tópico]"` ou `/recall [tópico]`

**Log:** Ao acrescentar entradas em `.state/log.md`, use estritamente o formato definido no `ZETTELBRAIN.md` (seção Convenção do log operacional). No cabeçalho use **`/recall`**. No corpo da entrada liste **todos** os caminhos relativos dos arquivos lidos em profundidade para compor a síntese (e `zettelbrain/index.md` e `zettelbrain/overview.md` quando lidos), além dos caminhos criados ou alterados quando houver fechamento de lacuna com nova nota permanente.

## Fluxo de Execução (Workflow)

### Etapa 1: Varredura e Leitura Profunda
1. Priorize a ferramenta MCP `ZettelBrain.search_zettelbrain` para recuperar candidatos por busca híbrida ou fallback lexical local. Se a ferramenta estiver indisponível, registre a indisponibilidade mentalmente e siga para a leitura manual por `zettelbrain/index.md`.
2. Use `ZettelBrain.list_zettelbrain_markdown` e `ZettelBrain.read_zettelbrain_markdown` para abrir os arquivos candidatos retornados. Se a ferramenta não estiver disponível, acesse e leia o arquivo `zettelbrain/index.md` para mapear todas as Notas Permanentes e Notas de Literatura que possuam relação semântica com o tópico solicitado.
3. Leia `zettelbrain/overview.md` para alinhar o dossiê com a síntese viva do cofre quando existir conteúdo útil.
4. Acesse e leia integralmente os arquivos identificados para absorver o contexto exato e as conexões armazenadas na base.
5. Quando notas de literatura relevantes referenciarem `raw/papers/` e existir cache PageIndex, use primeiro `ZettelBrain.resolve_pdf`, `ZettelBrain.inspect_pdf_manifest`, `ZettelBrain.list_pdf_manifests` ou `ZettelBrain.read_pdf_cache` para localizar `.pageindex/<document_id>/manifest.json` e buscar trechos por termo no `tree.json`. Se uma página específica for necessária, use `ZettelBrain.read_pdf_page(document_id, page)`. Se a ferramenta estiver indisponível, localize manualmente `.pageindex/<document_id>/manifest.json` cujo `source_path` coincida com o PDF. O `document_id` é o SHA-256 do binário conforme a secção **Instrumentação obrigatória: `document_id` (SHA-256)** no `ZETTELBRAIN.md`.
6. Use `.pageindex/<document_id>/tree.json` ou `ZettelBrain.read_pdf_page` apenas para localizar seções relevantes, confirmar a cobertura temática do paper e orientar um retorno seletivo à fonte primária. O cache PageIndex não deve ser tratado como base primária de afirmações conceituais, teóricas ou metodológicas no dossiê do `/recall`.
7. Quando a síntese depender de um detalhe não preservado com segurança nas notas do cofre, utilize o PageIndex para apontar a região relevante do paper e então confira a nota de literatura correspondente ou o PDF original antes de consolidar a afirmação.
8. Avalie explicitamente se o tópico solicitado já está coberto por pelo menos uma Nota Permanente adequada. Se existir apenas cobertura indireta, trate como lacuna parcial.

### Etapa 2: Síntese e Exposição (Aplicação Rigorosa de Estilo)
Apresente ao usuário um dossiê preliminar com os achados. A geração deste texto DEVE respeitar integralmente as Regras Globais de Estilo:
- É terminantemente proibido o uso de listas ou marcadores (bullet points).
- O texto deve ser contínuo e desenvolvido em parágrafos de prosa, sem gravar rótulos artificiais de seção no corpo do texto, apresentando o cenário consolidado da base sobre o tema, conectando os diferentes autores e dados lidos e sintetizando o panorama atual e eventuais lacunas.
- Utilize **negrito** exclusivamente para destacar constructos teóricos, variáveis matemáticas ou palavras-chave cruciais para a recuperação da informação.
- Não utilize travessões; construa a fluidez da explicação por meio de vírgulas e períodos curtos e diretos.
- O tom deve ser estritamente analítico e adequado para a absorção por uma audiência com vasta vivência corporativa e analítica.
- Cite as notas consultadas ao longo do texto utilizando obrigatoriamente a sintaxe `[[nome-do-arquivo]]`.

### Etapa 3: Validação Interativa
1. Ao final do texto estruturado, pergunte ao usuário se o dossiê abrange a direção que ele deseja explorar ou se é necessário incluir e excluir notas específicas da seleção atual.
2. Aguarde o direcionamento do usuário antes de dar a busca por concluída.

### Etapa 4: Fechamento de Lacuna no Cofre
1. Se a avaliação da Etapa 1 indicar lacuna total ou parcial em tema relevante para o cofre, crie uma **Nota Permanente** em `zettelbrain/permanent/` mesmo sem ingestão de nova fonte externa.
2. A nota criada deve seguir integralmente o padrão do `ZETTELBRAIN.md`: frontmatter de permanente, `# Título da nota` após o YAML, texto atômico em prosa contínua estruturado em parágrafos (sem impor número fixo de parágrafos e sem imprimir rótulos literais de seção), sem bullet points e com negrito apenas para conceitos-chave.
3. Ao criar a nova permanente, conecte o tema ao grafo com `[[wikilinks]]` para notas relacionadas já existentes. Quando houver duas ou mais candidatas claras, inclua pelo menos dois wikilinks no corpo da nota.
4. Atualize `zettelbrain/index.md` para incluir a nova nota na seção apropriada.
5. Se não houver notas relacionadas suficientes para cumprir ligação mínima, registre a limitação no `.state/log.md` nesta execução.

### Etapa 5: Log de Atividade
1. Atualize o arquivo `.state/log.md` com cabeçalho **`/recall`**, resumo do tópico pesquisado e **lista explícita** de todos os caminhos relativos lidos.
2. Quando houver criação de nota permanente por fechamento de lacuna, registre explicitamente os caminhos criados e alterados, incluindo a nota nova e `zettelbrain/index.md`.
