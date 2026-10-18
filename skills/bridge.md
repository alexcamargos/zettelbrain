# /bridge (Atrito Criativo e Fricção Semântica)

## Objetivo
Forçar conexões interdisciplinares e associações não óbvias entre conceitos semanticamente distantes do ZettelBrain, combatendo a criação de silos de conhecimento e estimulando novas frentes de modelagem ou pesquisa teórica.

## Gatilho
Acionado quando o usuário digitar `/bridge` ou disser `gemini "Execute a skill /bridge"` ou `gemini "Faça uma conexão de atrito criativo"`.

**Log:** Cada execução bem-sucedida que criar arquivos ou rascunhos deve ser registrada em `.state/log.md` usando o formato definido no `ZETTELBRAIN.md` (seção Convenção do log operacional). No cabeçalho use **`/bridge`**.

## Fluxo de Execução (Workflow)

### Etapa 1: Obtenção do Par de Notas Distantes
1. Invoque a ferramenta MCP `get_semantic_bridge` para buscar duas notas do cofre que possuam similaridade semântica baixa (usualmente entre 0.05 e 0.40).
2. Se a ferramenta retornar um erro ou indicar falta de documentos, interrompa a execução e informe ao usuário que o cofre precisa de pelo menos duas notas indexadas para rodar a fricção semântica.
3. Se o par for retornado com sucesso, leia o conteúdo integral de ambas as notas (Nota A e Nota B) usando a ferramenta MCP de leitura.

### Etapa 2: Formulação da Síntese Unificadora (Aplicação Rigorosa de Estilo)
Redija uma proposta de unificação conceitual ou modelagem híbrida para as duas notas identificadas. O texto gerado deve seguir estritamente as **Regras Globais de Estilo**:
- Escrita exclusivamente em Português do Brasil (PT-BR).
- É terminantemente proibido o uso de listas ou marcadores (bullet points).
- Desenvolva o texto em parágrafos contínuos de prosa, sem usar rótulos artificiais de seção e sem impor número fixo de parágrafos, apresentando as duas notas parceiras de ponte com seus conceitos-chave, evidenciando o "atrito criativo" original entre elas e propondo a síntese unificadora, ponto de tangência teórico, modelagem híbrida aplicável ou hipótese de investigação que integre ambos os conceitos.
- Use **negrito** exclusivamente para destacar constructos teóricos, variáveis analíticas, nomes de algoritmos e métricas técnicas centrais.
- Não utilize travessões; garanta a coesão textual por meio de vírgulas e períodos diretos.
- Não utilize emojis.
- Mantenha o tom altamente formal, intelectual e analítico.
- Aplique a camada de polimento da skill `/humanizer` para eliminar fórmulas artificiais de IA, mantendo o limite de 4 frases por parágrafo e cadência orgânica.

### Etapa 3: Persistência e Gravação de Rascunho
1. Formate a síntese gerada com um frontmatter YAML simplificado contendo:
   ```yaml
   ---
   type: draft
   id: YYYYMMDDHHMM
   title: "Ponte Semântica: Título da Nota A e Título da Nota B"
   references: [[nome-exato-da-nota-a]], [[nome-exato-da-nota-b]]
   ---
   ```
   Adicione em seguida um H1 com o título da ponte semântica e os parágrafos de prosa dissertativa gerados.
2. Salve o arquivo na pasta `zettelbrain/drafts/` com o nome formatado em minúsculas e separado por hifens: `bridge-[slug-da-nota-a]-e-[slug-da-nota-b].md` (substituindo acentos e caracteres especiais).
3. Adicione o link para o rascunho criado na seção correspondente do `zettelbrain/index.md` (sob a seção de Rascunhos).
4. Atualize o arquivo `.state/log.md` com a entrada de log sob a tag **`/bridge`**, detalhando o caminho do rascunho gerado, os arquivos lidos como insumos e o valor de similaridade cosseno retornado pelo servidor.
