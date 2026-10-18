# /visual (Geração de Ativos Visuais e Gráficos)

## Objetivo
Transformar o conhecimento previamente validado em representações visuais estruturadas, como fluxogramas, gráficos analíticos ou diagramas conceituais, armazenando os ativos nos diretórios corretos de anexos e recursos visuais.

## Gatilho
Acionado quando o usuário disser `gemini "Execute a skill /visual para criar [tipo_de_ativo] sobre [tópico]"` ou `/visual [tipo_de_ativo] [tópico]`

**Log:** Ao acrescentar entradas em `.state/log.md`, use estritamente o formato definido no `ZETTELBRAIN.md` (seção Convenção do log operacional). No cabeçalho use **`/visual`**. No corpo liste **todos** os caminhos relativos de arquivos **criados ou alterados** e das notas lidas como insumo.

## Fluxo de Execução (Workflow)

### Etapa 1: Validação do Escopo
1. Certifique-se de que o contexto base já foi estabelecido (preferencialmente validado através da skill `/recall`). Leia as notas especificadas para compreender a lógica, as variáveis ou as etapas do processo que serão ilustradas.

### Etapa 2: Execução Técnica do Ativo
De acordo com a solicitação, execute estritamente uma das rotinas abaixo:

**A. Para gráficos e fluxogramas (Mermaid):**
1. Escreva o diagrama em **Mermaid** (linguagem de diagramas, não confundir com o pacote JavaScript `mermaid` usado por renderizadores). Inclua o código dentro de um fence Markdown com rótulo `mermaid` na primeira linha após as três crases de abertura, para que editores como o Obsidian renderizem corretamente fluxos, arquiteturas de dados, árvores de decisão ou métricas.
2. Salve o conteúdo completo da nota (texto explicativo conforme Etapa 3 mais o fence Mermaid) em um novo arquivo Markdown em `zettelbrain/visual/fluxograma-[tópico].md`.

**B. Para imagens descritivas:**
1. Descreva um prompt de geração de imagem altamente técnico, ou gere o arquivo e proceda com o salvamento no diretório padrão de anexos `zettelbrain/assets/`.

**C. Para slides (Marp):**
1. Gere o conteúdo no formato **Marp** (separadores de slide e metadados conforme a sintaxe Marp e a convenção do projeto; evite confundir com o frontmatter YAML das notas Zettelkasten em outros diretórios).
2. Salve o arquivo em `zettelbrain/presentations/apresentacao-[tópico].md`. O texto explicativo de apoio segue a Etapa 3 na mesma nota ou em nota irmã em `zettelbrain/visual/`, conforme fizer sentido para o cofre.

### Etapa 3: Síntese Explicativa (Aplicação Rigorosa de Estilo)
Todo ativo gerado DEVE ser acompanhado de um texto explicativo na nota correspondente. A redação DEVE obedecer integralmente às **Regras Globais de Estilo**:
- É terminantemente proibido o uso de listas ou marcadores (bullet points).
- Desenvolva a explicação em parágrafos contínuos de prosa, sem gravar rótulos artificiais de seção e sem impor número fixo de parágrafos, apresentando o que o gráfico ou imagem representa e o problema que ilustra, mostrando como as variáveis operam dentro da estrutura demonstrada e analisando o impacto no modelo estudado.
- Aplique **negrito** exclusivamente para destacar variáveis de modelo, métricas financeiras ou conceitos-chave.
- Construa a fluidez da explicação por meio de vírgulas e períodos curtos. Não utilize travessões.
- Não utilize emojis.
- O tom deve ser estritamente analítico e adequado para a absorção por uma audiência corporativa experiente.

### Etapa 4: Catalogação
1. Adicione o link semântico do novo arquivo gerado ao `zettelbrain/index.md`.
2. Atualize o `.state/log.md` com cabeçalho **`/visual`**, tipo de ativo gerado, e **lista explícita** de caminhos relativos (notas lidas, arquivo visual ou Marp, `index.md` se alterado, assets se criados).
