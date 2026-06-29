# /lint (Manutenção e Saúde do ZettelBrain)

## Objetivo
Auditar a integridade estrutural e teórica do diretório `zettelbrain/`, identificando falhas de conexão, contradições acadêmicas e oportunidades de expansão teórica, **regenerar a síntese viva** em `zettelbrain/overview.md` e gravar relatório de manutenção, garantindo a alta confiabilidade da base de conhecimento.

## Gatilho
Acionado quando o usuário disser `gemini "Execute a skill /lint no diretório zettelbrain/"` ou `/lint zettelbrain/`

**Log:** Ao acrescentar entradas em `.state/log.md`, use estritamente o formato definido no `ZETTELBRAIN.md` (seção Convenção do log operacional). No cabeçalho use **`/lint`**.

## Fluxo de Execução (Workflow)

### Etapa 1: Varredura de Integridade (Links e Estrutura)
1. Execute a ferramenta MCP local `lint_zettelbrain` para realizar a auditoria estática e estrutural do cofre de forma determinística e rápida.
2. Utilize o payload JSON de saída da ferramenta (contendo `errors`, `warnings`, `fixes` e `emergent_patterns`) para fundamentar as análises estruturais de:
   - **Links Mortos** (`errors` do tipo `dead_link`)
   - **Notas Órfãs** (`warnings` do tipo `orphan_note`)
   - **Ligação Mínima ao Grafo** (`warnings` do tipo `minimal_connection`)
   - **Referências a notas deprecadas** (`warnings` do tipo `deprecated_reference`)
   - **Nomes de notas de literatura fora do padrão** (`warnings` do tipo `literature_filename_pattern`, quando a correção automática não puder ser aplicada)
   - **Correções automáticas de nomes de notas de literatura** (`fixes` do tipo `literature_filename`)
   - **Padrões Emergentes** (lista em `emergent_patterns`)
3. **Evite ler todas as notas em profundidade** no contexto apenas para verificar ligações estruturais ou listar negritos, reduzindo drasticamente o consumo de tokens de contexto do LLM.

### Etapa 2: Auditoria Teórica (Contradições e Obsolescência)
1. Cruze as afirmações das notas mais antigas com as fontes mais recentes recém-ingestadas.
2. Sinalize afirmações obsoletas ou superadas pela literatura recente.
3. Destaque contradições teóricas diretas entre autores diferentes.
4. Liste notas com `deprecated: true` como **arquivo histórico** válido; sugira revisão humana se estiverem ainda muito ligadas ao grafo ativo sem `superseded_by`.

### Etapa 3: Regeneração do `overview.md`
1. Leia `zettelbrain/index.md` e amostre o mínimo necessário de notas representativas para não contradizer o cofre.
2. **Sobrescreva** `zettelbrain/overview.md` com três parágrafos contínuos, em PT-BR, sem bullet points no corpo e sendo terminantemente proibido gravar os rótulos literais "Introdução", "Contexto" ou "Fechamento", refletindo: domínios cobertos, volume aproximado, riscos (fontes web de **confidence** baixa, lacunas de ligação), e próximos passos de exploração em prosa.
3. Preserve no frontmatter do `overview.md` o par `type: overview` e o campo `id: overview`; pode atualizar um campo `updated` with a data ISO de hoje se julgar útil.

### Etapa 4: Elaboração do Relatório de Manutenção (Aplicação Rigorosa de Estilo)
Gere um relatório de diagnóstico e salve como `zettelbrain/syntheses/relatorio-manutencao-[data].md`. A redação deste documento DEVE obedecer integralmente às **Regras Globais de Estilo**:
- É terminantemente proibido o uso de listas ou marcadores (bullet points).
- Estruture o relatório em três parágrafos contínuos, sendo terminantemente proibido gravar os rótulos literais "Introdução", "Contexto" ou "Fechamento" no corpo do texto:
  - O **primeiro parágrafo** deve apresentar o estado geral da base e o volume de anotações integradas;
  - O **segundo parágrafo** deve descrever detalhadamente as contradições teóricas encontradas, notas órfãs identificadas, padrões emergentes, sugestões de ligação mínima ao grafo e notas deprecadas relevantes;
  - O **terceiro parágrafo** (conclusão) deve resumir as ações sugeridas e definir no mínimo três lacunas de pesquisa a serem exploradas nas próximas sessões.
- Aplique **negrito** exclusivamente para destacar as palavras-chave, variáveis, anomalias encontradas e conceitos centrais.
- Não utilize travessões; garanta a fluidez da leitura por meio de vírgulas e períodos curtos e diretos.
- Não utilize emojis.
- Mantenha o tom estritamente analítico e adequado para a validação de pesquisas em nível de pós-graduação.

### Etapa 5: Atualização de Sistema
1. Adicione o link semântico do novo relatório à respectiva seção no `zettelbrain/index.md` (se ainda não existir seção para relatórios de manutenção, crie a linha na seção **Sínteses e relatórios**).
2. Garanta que `zettelbrain/index.md` continue a apontar para **[[overview]]** conforme o modelo do índice.
3. Atualize o `.state/log.md` com cabeçalho **`/lint`** e **lista explícita** de todos os caminhos relativos criados ou alterados (relatório em `syntheses/`, `zettelbrain/overview.md`, `zettelbrain/index.md`, e quaisquer notas cuja leitura integral foi necessária para a auditoria).
