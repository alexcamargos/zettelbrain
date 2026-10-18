# /research-deep (Pesquisa Acadêmica de Lacunas)

## Objetivo
Mapear lacunas conceituais identificadas no cofre ou especificadas pelo usuário e realizar buscas ativas em bases de dados científicas globais de impacto (arXiv, OpenAlex, PubMed, etc.) utilizando os conectores locais disponíveis. O fluxo compila resumos e gera recomendações de leitura automatizadas para direcionar a ingestão de novas fontes primárias.

## Gatilho
Acionado quando o usuário digitar `/research-deep [termo]` ou disser `gemini "Execute a skill /research-deep para X"`.

**Log:** O registro do comando no final da sessão deve constar em `.state/log.md` sob o cabeçalho **`/research-deep`**, seguindo estritamente as regras de logging do projeto.

## Fluxo de Execução (Workflow)

### Etapa 1: Mapeamento de Tema e Formulação de Query
1. Identifique o termo de busca acadêmica. Se o comando for executado sem termo explícito, o agente deve ler o relatório de manutenção mais recente em `zettelbrain/syntheses/` para extrair as lacunas de pesquisa listadas em aberto na conclusão do `/lint`.
2. Formule uma query de busca científica combinando palavras-chave em inglês e operadores lógicos (e.g., AND, OR) adequados para bases científicas.

### Etapa 2: Consulta às Bases de Dados de Impacto
1. Utilize as ferramentas e skills de ciência disponíveis no ambiente:
   - Invoque `literature-search-openalex` ou `literature-search-arxiv` como primeira opção para modelagem quantitativa, matemática aplicada, inteligência artificial e economia de crédito.
   - Invoque `pubmed-database` ou `literature-search-europepmc` para assuntos de saúde, ensaios clínicos e bioquímica (se aplicável).
2. Extraia os metadados dos 3 artigos mais relevantes e de maior impacto bibliométrico (citações, relevância temática, ano recente), capturando título, autores, resumo (abstract), ano e o identificador DOI ou link do PDF.

### Etapa 3: Elaboração do Relatório de Recomendações (Aplicação Rigorosa de Estilo)
Redija um relatório detalhando os resultados obtidos. O texto deve seguir rigorosamente as **Regras Globais de Estilo**:
- Escrita exclusivamente em Português do Brasil (PT-BR).
- É terminantemente proibido o uso de listas ou marcadores (bullet points).
- Desenvolva o corpo do texto em parágrafos contínuos de prosa, sem usar rótulos artificiais de seção e sem impor número fixo de parágrafos, descrevendo a lacuna conceitual ou o tema consultado no contexto atual da pesquisa do cofre, apresentando e correlacionando as conclusões, variáveis e metodologias dos 3 artigos selecionados, e apontando qual dos artigos deve ser baixado para a pasta `raw/papers/` e processado prioritariamente via `/paper`.
- Use **negrito** exclusivamente para destacar constructos teóricos, variáveis analíticas, nomes de algoritmos e métricas técnicas centrais.
- Não utilize travessões ou emojis.
- O tom deve ser rigoroso, analítico e de alto nível acadêmico.

### Etapa 4: Gravação do Relatório e Atualização do Sistema
1. Formate o relatório como um rascunho em `zettelbrain/drafts/pesquisa-profunda-[slug-da-query]-[data].md`. Insira no topo do arquivo um frontmatter YAML seguido de título H1:
   ```yaml
   ---
   type: draft
   id: YYYYMMDDHHMM
   title: "Relatório de Pesquisa Profunda: [Query]"
   retrieved_at: "AAAA-MM-DD"
   confidence: medium
   ---
   ```
2. Adicione o link semântico do novo arquivo na seção de **Rascunhos** do índice em `zettelbrain/index.md`.
3. Atualize o `.state/log.md` sob a tag **`/research-deep`**, documentando o termo pesquisado, as APIs científicas acionadas, os títulos dos 3 artigos obtidos e o caminho relativo do arquivo gerado em `zettelbrain/drafts/`.
4. Caso o relatório recomende o download do PDF completo, insira o lembrete de download em `.state/hot.md`.
