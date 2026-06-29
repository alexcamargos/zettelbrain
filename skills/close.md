# /close (Encerramento e Empacotamento de Sessão)

## Objetivo
Sintetizar as descobertas da janela de estudos, atualizar o cache de contexto contínuo e preparar o ambiente estrutural para a próxima sessão, garantindo que o conhecimento acumulado e as decisões metodológicas não se percam.

## Gatilho
Acionado quando o usuário disser `gemini "Execute a skill /close"` ou `gemini "Encerre a sessão"` ou `/close`

**Log:** Ao acrescentar a entrada final de encerramento (e eventuais retificações) em `.state/log.md`, use estritamente o formato definido no `ZETTELBRAIN.md` (seção Convenção do log operacional).

## Fluxo de Execução (Workflow)

### Etapa 1: Consolidação ancorada em arquivos (obrigatório)
O histórico do chat pode estar incompleto ou ter sido reiniciado. **Não confie na memória da conversa como fonte primária.**

1. Leia **na íntegra** o arquivo `.state/log.md` antes de redigir qualquer síntese.
2. Delimite o intervalo desta sessão no log: utilize **todas as entradas posteriores** à última linha de cabeçalho que registre um encerramento anterior (por exemplo um título `##` contendo `/close` ou a expressão usada na convenção deste repositório para fim de sessão). Se não existir encerramento anterior, considere o arquivo completo.
3. Leia também `.state/hot.md` para alinhar com o cache já gravado antes deste `/close`.
4. Liste mentalmente as operações desta sessão **somente** com base nesse intervalo do log (ingestões, `/paper`, `/paper-intro`, `/article`, `/youtube`, `/recall`, `/trace`, `/ghost`, `/visual`, `/lint`, etc.), incluindo geração ou reuso de cache em **`.pageindex/`** quando constar no log. **É proibido inventar** operações, caminhos de arquivos ou resultados que não apareçam escritos no log.
5. Decisões metodológicas para o `hot.md` devem estar **suportadas** pelo log nesse intervalo ou por instruções **explícitas e inequívocas** do usuário neste mesmo chat. Se o chat mencionar trabalho relevante que **não** conste no log, não trate isso como fato consolidado: descreva a lacuna de forma neutra numa frase no **Fechamento** do `hot.md` e registre-a na entrada final do log (Etapa 3).

### Etapa 2: Atualização do Cache de Sessão e Colheita (Aplicação Rigorosa de Estilo)
1. Sobrescreva o conteúdo atual do arquivo `.state/hot.md` com um novo panorama da pesquisa. A redação deste documento DEVE obedecer integralmente às **Regras Globais de Estilo**:
   - É terminantemente proibido o uso de listas ou marcadores (bullet points).
   - O texto completo não deve ultrapassar 500 palavras e deve ser estruturado em três parágrafos contínuos, sendo terminantemente proibido gravar os rótulos literais "Introdução", "Contexto" ou "Fechamento" no corpo do texto:
     - O **primeiro parágrafo** deve apresentar o foco atual de pesquisa estabelecido nesta sessão;
     - O **segundo parágrafo** deve descrever as decisões metodológicas tomadas e as variáveis validadas;
     - O **terceiro parágrafo** (conclusão) deve apontar claramente as questões em aberto e a primeira tarefa recomendada para a próxima sessão de estudo ou pesquisa, sem assumir horário ou calendário fixos. Se o log da sessão registrar trabalho com PageIndex, integre em prosa o **document_id** ou o foco do paper conforme constar no log, sem listas.
   - Aplique **negrito** exclusivamente para destacar constructos teóricos, variáveis estatísticas, nomes de algoritmos e métricas financeiras.
   - Não utilize travessões. Empregue vírgulas e períodos curtos e diretos para garantir a fluidez da leitura.
   - Não utilize emojis.
   - O tom deve permanecer estritamente analítico e compatível com a gestão de projetos de Data Science e pesquisa acadêmica avançada.

2. **Colheita de Sessão (Session Harvesting):** Escaneie o diálogo da sessão para extrair conceitos estruturados, algoritmos, decisões de parametrização ou hipóteses científicas debatidas. Se identificar conhecimento maduro não consolidado, salve tais formulações como arquivos de rascunho em `zettelbrain/drafts/` no formato de prosa dissertativa com frontmatter contendo `type: draft` e `id: YYYYMMDDHHMM`, citando o rascunho como pendência de refinamento acadêmico no último parágrafo de `.state/hot.md`.

### Etapa 3: Auditoria Final e Log
1. Releia o intervalo da sessão em `.state/log.md` (conforme Etapa 1). Se faltar registro de alguma operação que o próprio log ou o chat demonstrem claramente que ocorreu, **acrescente entradas retroativas resumidas** antes do encerramento, com data e descrição mínima, em vez de omitir o fato.
2. Acrescente no **final** do arquivo uma entrada de encerramento com cabeçalho `##` em linha própria, contendo a data, a menção explícita a `/close` e um resumo: operações cobertas pelo log nesta sessão, arquivos tocados, criados ou gerados em `drafts/` pela colheita, e lacunas encontradas.
