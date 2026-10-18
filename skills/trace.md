# /trace (Rastreio Teórico e Evolução Cronológica)

## Objetivo
Vasculhar todo o diretório `zettelbrain/` em busca de todas as menções a um conceito específico, reconstruindo cronologicamente como a compreensão acadêmica ou de mercado sobre este tema evoluiu ao longo das datas de publicação dos artigos ingestados. O resultado final é um dossiê analítico que mapeia consensos, divergências e saltos metodológicos.

## Gatilho
Acionado quando o usuário disser `gemini "Execute a skill /trace sobre [conceito_ou_variavel]"` ou `/trace [conceito_ou_variavel]`

**Log:** Ao acrescentar entradas em `.state/log.md`, use estritamente o formato definido no `ZETTELBRAIN.md` (seção Convenção do log operacional). No cabeçalho use **`/trace`**. No corpo liste o conceito rastreado, o arquivo de síntese criado ou atualizado, alterações em `index.md` se houver, e **todos** os caminhos relativos das notas lidas na varredura.

## Fluxo de Execução (Workflow)

### Etapa 1: Mineração e Ordenação Cronológica
1. Percorra os diretórios `zettelbrain/literature/` e `zettelbrain/permanent/` identificando todas as notas que mencionam o conceito solicitado.
2. Extraia o ano de publicação das fontes (campo `year` no frontmatter das Notas de Literatura). Para Notas Permanentes, use o campo `year` se existir; caso contrário use o prefixo numérico do campo `id` (YYYYMMDDHHMM) como **proxy cronológico** quando fizer sentido, ou declare no dossiê que a ordenação dessas entradas é aproximada.
3. Ordene as informações extraídas do dado mais antigo para o mais recente, estabelecendo a linha do tempo da evolução teórica.

### Etapa 2: Elaboração do Dossiê Evolutivo (Aplicação Rigorosa de Estilo)
Gere um dossiê analítico consolidando os achados. A redação deste documento DEVE obedecer integralmente às **Regras Globais de Estilo**:
- É terminantemente proibido o uso de listas ou marcadores (bullet points).
- Desenvolva a redação em parágrafos contínuos de prosa, sem gravar rótulos artificiais de seção e sem impor um número fixo de parágrafos, apresentando o conceito rastreado e o recorte temporal analisado, reconstruindo a narrativa cronológica de como o conceito foi tratado pelos primeiros autores, suas mutações e divergências na literatura, e sintetizando o entendimento atual sobre o tema.
- Aplique a Técnica Feynman com foco em clareza lógica para executivos seniores; traduza o peso matemático ou estatístico da evolução do conceito sem perder a profundidade analítica.
- Aplique **negrito** exclusivamente para destacar constructos teóricos, variáveis, métricas, autores e anos-chave.
- Não utilize travessões. A fluidez da explicação deve ser garantida pelo uso de vírgulas e períodos curtos e diretos.
- Não utilize emojis.
- Todo artigo ou nota mencionada na evolução histórica deve ser devidamente linkada no corpo do texto utilizando a sintaxe `[[nome-do-arquivo]]`.
- Aplique obrigatoriamente a camada de polimento da skill `/humanizer`: elimine clichês de LLM, gerúndios vazios de cauda e falsos contrastes, mantendo parágrafos de até 4 frases e cadência variada (burstiness) para alta legibilidade humana.

### Etapa 3: Salvamento e Indexação
1. Salve o dossiê evolutivo completo em um novo arquivo no diretório `zettelbrain/syntheses/trace-[conceito].md`.
2. Adicione o link semântico do novo documento ao arquivo `zettelbrain/index.md` na seção correspondente a sínteses e comparações.
3. Atualize o arquivo `.state/log.md` com cabeçalho **`/trace`**, conceito analisado, caminho do dossiê em `syntheses/`, e **lista explícita** de cada nota cujo conteúdo foi lido integralmente ou em parte substantiva para a cronologia.
