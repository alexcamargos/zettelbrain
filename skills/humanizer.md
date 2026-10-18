# /humanizer (Filtro e Humanização de Conteúdo em PT-BR)

## Objetivo
Atuar como um linter estilístico e editor implacável para eliminar vícios sintáticos, lexicais e estruturais típicos de modelos de linguagem (LLMs), garantindo uma prosa fluida, natural, concisa e autoral em Português do Brasil (PT-BR). Esta skill opera sob demanda direta (revisando textos, notas ou rascunhos fornecidos pelo usuário) e atua como camada canônica obrigatória de polimento final para qualquer conteúdo dissertativo gerado pelas demais skills do cofre (`/ghost`, `/paper`, `/article`, `/youtube`, `/trace`, `/bridge`).

## Gatilho
1. **Chamada Direta:** Acionado quando o usuário disser `gemini "Execute a skill /humanizer no arquivo [caminho]"` ou `/humanizer [caminho_do_arquivo]` ou solicitar explicitamente humanização/revisão de um texto.
2. **Invocação em Pipeline (Camada Final):** Executado obrigatoriamente logo após a validação factual da skill `/fact-check`, antes de finalizar qualquer nota ou rascunho dissertativo gerado pelas skills de produção e ingestão de conteúdo no cofre.

**Log:** Ao acrescentar entradas em `.state/log.md`, use estritamente o formato definido no `ZETTELBRAIN.md` (seção Convenção do log operacional). No cabeçalho use **`/humanizer`**. Liste todos os caminhos relativos de arquivos analisados, alterados ou criados.

## Fluxo de Execução (Workflow)

### Etapa 1: Preservação de Metadados e Conexões Semânticas
1. **Isolamento de Frontmatter:** Se o arquivo contiver frontmatter YAML entre `---`, preserve intactas todas as chaves e valores (`type`, `id`, `sources`, `confidence`, `abnt_reference`, etc.).
2. **Blindagem de Wikilinks:** Nunca altere o alvo interno de `[[wikilinks]]`. Preserve nomes de notas canônicos e citações em conformidade com o padrão Obsidian.
3. **Proteção Factual Estrita:** Mantenha todas as afirmações sustentadas pelo texto original, pelas notas do cofre e validadas pelo `/fact-check`. NUNCA invente fatos, dados estatísticos, fórmulas, datas ou nomes para tentar deixar a frase mais elegante.
4. **Termos Técnicos e Negritos:** Preserve o destaque em negrito (`**termo**`) para constructos teóricos, variáveis de modelo e termos técnicos centrais, conforme o `ZETTELBRAIN.md`.

### Etapa 2: Regras Mecânicas e de Pontuação
1. **Proibição Absoluta de Travessões Explicativos:** Elimine qualquer travessão (`—`) ou meia-risca (`–`) usado para intercalar explicações. Substitua por vírgulas, parênteses ou divida em períodos curtos com ponto final. Preserve traços e hífens exclusivamente dentro de blocos de código, comandos, fórmulas, caminhos e URLs.
2. **Zero Emojis e Símbolos Decorativos:** Elimine emojis, setas estilizadas (`→`, `⇒`) ou caracteres decorativos. Use caixa normal de frase (Sentence case) em subtítulos.
3. **Teto de 4 Frases por Parágrafo:** Nenhum parágrafo deve ultrapassar 4 frases. Mantenha os blocos visuais enxutos para leitura rápida por humanos.
4. **Variação de Cadência (Burstiness):** Intercale frases analíticas médias (20 a 30 palavras) com frases curtas e diretas (3 a 8 palavras) para arrematar conclusões lógicas.
5. **Prosa Acima de Listas Automáticas:** Converta bullet points mecânicos (`- **Conceito:** explicação`) em parágrafos contínuos de prosa articulada. Listas com hífens são proibidas no corpo das notas de `zettelbrain/` (reservadas unicamente ao `zettelbrain/index.md`).
6. **Integração Fluida de Números:** Integre números na prosa usando proporções claras e diretas, sem acumular tabelas desnecessárias quando um período resolver a comparação.
7. **Padrão Culto Direto (Sem Oralidade Coloquial):** Mantenha o padrão culto executivo e acadêmico da técnica Feynman exigida pelo `ZETTELBRAIN.md`. Não utilize gírias ou contrações orais coloquiais (como "pra", "tá", "a gente"). A naturalidade humana deve vir da clareza e ritmo das frases, não do coloquialismo informal.

### Etapa 3: Supressão de Vícios Estruturais e Encenatórios
1. **Falsos Profundos e Contrastes Vazios ("Não é X, é Y"):** Elimine fórmulas como `"Não é apenas sobre X, mas sim sobre Y"`, `"Mais do que X, trata-se de Y"`, ou caudas negativas soltas (`"...sem atalhos"`). Afirme a tese ou o mecanismo positivo diretamente.
2. **Gerúndios Explicativos de Cauda:** Corte orações no gerúndio coladas ao final de frases para forçar relevância (`"...destacando a importância de..."`, `"...garantindo maior consistência..."`, `"...refletindo o compromisso..."`). Encerre a frase no fato concreto ou declare a consequência prática em período separado.
3. **Tríades Forçadas:** Remova o hábito de LLMs de agrupar termos ou argumentos de três em três (`"rápido, seguro e escalável"`). Use três itens apenas quando houver exatamente três componentes reais; caso contrário, mantenha os elementos necessários ou aprofunde o argumento central.
4. **Intervalos Falsos ("De X a Y"):** Elimine intervalos metafóricos sem escala mensurável (`"da estratégia à execução"`, `"da concepção ao impacto"`). Utilize `"de X a Y"` exclusivamente para grandezas mensuráveis, temporais ou espaciais.
5. **Fuga de Variação Elegante:** Não substitua um substantivo técnico preciso por sinônimos rebuscados no mesmo trecho para evitar repetição artificial. A consistência terminológica é mandatória para a rede de notas atômicas do Zettelkasten.
6. **Fechamentos de Efeito e Frases de Impacto Vazias:** Remova parágrafos de uma linha só criados para soar profundos (`"E esse é o ponto."`, `"Pense nisso."`, `"O cenário mudou."`). Frases curtas devem conter um fato ou dedução lógica concreta.
7. **Espantalhos Retóricos e Autoridade Vaga:** Remova defesas preventivas contra objeções inexistentes (`"Não se trata de negar a importância de X, mas..."`) e apelos a fontes invisíveis (`"Especialistas apontam"`, `"Estudos indicam"`). Sustente o argumento pela mecânica causal e pelos dados da nota.
8. **Locuções Pomposas e Rodeios Verbais:**
   - Substitua locuções como `"atua como"`, `"serve como"`, `"opera como"` e `"conta com"` pelos verbos diretos **é**, **são** e **possui/tem**.
   - Substitua preenchimentos burocráticos: `"com o objetivo de"` por `"para"`; `"devido ao fato de que"` por `"porque"`; `"no presente momento"` por `"agora"`; `"ter a capacidade de"` por `"poder"`.

### Etapa 4: Lista Negra de Clichês Lexicais (Banimento Estrito)
- **Aberturas de IA:** "No cenário atual", "No mundo dinâmico de hoje", "Na era da informação", "Não é segredo que", "Vamos mergulhar", "Vamos examinar".
- **Aforismos Ocos:** "No seu cerne", "A verdadeira questão é", "O que realmente importa é", "Na essência".
- **Metáforas Gastas:** "Mergulho profundo" (deep dive), "Desbloquear o potencial", "Navegar pelo cenário", "Faca de dois gumes", "Tapeçaria", "Mosaico", "Sinfonia", "Virada de chave", "Game changer", "Alavancar" (sentido figurado), "Ressaltar", "Sublinhar", "Fomentar", "Potencializar".
- **Adjetivos Histriônicos:** "Crucial", "Fundamental", "Pivotal", "Revolucionário", "Fascinante", "Incrível", "Imprescindível", "Disruptivo", "Robusto" (fora de contexto estritamente estatístico/computacional formal).
- **Conectivos Engessados:** "Outrossim", "Ademais", "Destarte", "Por conseguinte", "Vale ressaltar que", "É importante notar que", "Cabe destacar".
- **Fechamentos Otimistas de IA:** "Em suma", "Em resumo", "Concluindo", "O futuro parece promissor", "Tempos empolgantes estão por vir". Termine sempre no último fato ou implicação analítica concreta.
- **Resíduos de Assistente:** Elimine saudações, desculpas, elogios ao usuário ou comentários sobre a resposta ("Espero que ajude", "Com certeza", "Excelente pergunta").

### Etapa 5: Auto-Auditoria pelos 8 Testes Finais
Antes de gravar qualquer texto no cofre, passe a redação pelos seguintes testes:
1. **Teste do Fato Inicial:** A primeira frase abre com um problema, fato ou dado concreto, em vez de uma definição vazia ou repetição do título?
2. **Teste Anti-Lero-Lero:** Se trocarmos o conceito por outro tema qualquer, o texto continua fazendo sentido superficial? Se sim, reescreva com o mecanismo causal específico.
3. **Varredura de Pontuação Proibida:** Existe algum travessão explicativo (`—` ou `–`) no texto?
4. **Corte de Caudas:** Há orações subordinadas terminando em gerúndio vago (`"...garantindo..."`)?
5. **Precisão Terminológica:** Os termos técnicos estão consistentes e sem sinônimos decorativos desnecessários?
6. **Ritmo e Diagramação:** Nenhum parágrafo passa de 4 frases? Não há marcadores ou listas com negrito e dois-pontos no corpo da nota?
7. **Integridade Factual e Wikilinks:** Todos os `[[wikilinks]]`, dados e fontes foram preservados intactos?
8. **Fechamento Seco:** O texto encerra em uma constatação técnica conclusiva, sem discursos de encerramento?

### Etapa 6: Gravação e Atualização de Log
1. **Sob Demanda:** Se executado diretamente sobre um arquivo existente, atualize o arquivo alvo no disco (ou salve a versão revisada conforme acordado com o usuário).
2. **Em Pipeline:** Integre o texto limpo ao arquivo gerado pela respectiva skill (`zettelbrain/drafts/`, `zettelbrain/literature/`, `zettelbrain/permanent/`, `zettelbrain/syntheses/`).
3. **Log Operacional:** Registre a ação em `.state/log.md` com cabeçalho **`/humanizer`** e a lista dos arquivos lapidados.
