# /fact-check (Auditoria Adversarial de Fatos e Lógica)

## Objetivo
Atuar como um crítico hostil e verificador implacável (*adversarial fact-checker*) para auditar rascunhos, notas e sínteses do ZettelBrain antes de sua publicação ou consolidação no cofre. O foco é identificar dados incorretos, números imprecisos, links mortos, citações atribuídas indevidamente, anacronismos, estatísticas enviesadas, saltos lógicos, premissas frágeis e alucinações de modelos de linguagem. Esta skill opera sob demanda direta e como camada canônica de auto-correção factual em pipeline pós-geração, antecedendo imediatamente o polimento estilístico da skill `/humanizer`.

## Gatilho
1. **Chamada Direta:** Acionado quando o usuário disser `gemini "Execute a skill /fact-check no arquivo [caminho]"` ou `/fact-check [caminho_do_arquivo]` ou solicitar explicitamente checagem de fatos, destruição lógica ou auditoria pré-publicação de um texto.
2. **Invocação em Pipeline (Camada de Validação Factual):** Executado obrigatoriamente logo após a geração de notas ou rascunhos dissertativos pelas skills de produção e ingestão (`/ghost`, `/paper`, `/article`, `/youtube`, `/trace`, `/bridge`), antes da submissão do texto ao `/humanizer`.

**Log:** Ao acrescentar entradas em `.state/log.md`, use estritamente o formato definido no `ZETTELBRAIN.md` (seção Convenção do log operacional). No cabeçalho use **`/fact-check`**. Liste todos os caminhos relativos de arquivos auditados, corrigidos e as notas ou fontes primárias lidas como referência.

## Princípios Inegociáveis (Non-Negotiables)

1. **Opiniões e Teses Centrais Blindadas:** Nunca altere, suavize ou redirecione a tese, opinião ou linha analítica do autor sem confirmação expressa. Se um fato comprovadamente incorreto for a premissa indispensável da tese central (*deal breaker*), interrompa o fluxo automático: sinalize o conflito na seção de confirmação prévia e aguarde a decisão humana.
2. **Auto-Correção (Auto-Fix) no Pass 1:** Aplique de imediato todas as correções factuais objetivas que não desmoronem a conclusão lógica do texto: números corrigidos, datas, nomes próprios, atribuições corretas de autoria, links ou afirmações que possam ser respaldadas ou enxugadas. Apenas os *deal breakers* aguardam o usuário.
3. **Duplo Ancoramento de Evidências (Cofre + Fontes Primárias):**
   - **Ancoramento Interno:** Citações teóricas, autores e relações conceituais devem refletir rigorosamente o conteúdo das notas de literatura (`zettelbrain/literature/`), artigos (`raw/articles/`) e papers originais (`raw/papers/`).
   - **Ancoramento Externo:** Dados estatísticos, métricas e alegações empíricas externas sustentam-se exclusivamente em evidências primárias oficiais (papers revisados por pares, documentação técnica oficial, dados governamentais ou relatórios canônicos), nunca em blogs de SEO ou fóruns sem checagem.
4. **Estilo não é Fato:** Sarcasmo, provocação, tom autoral ou pressuposição de conhecimento prévio do leitor só devem ser apontados se quebrarem a coerência lógica estrita do argumento. O refinamento de clichês e ritmo cabe à skill `/humanizer`.
5. **Blindagem de Metadados e Wikilinks:** Preserve intactos o frontmatter YAML e o destino exato de todos os `[[wikilinks]]`. Se um wikilink apontar para um conceito inexistente, aponte como imprecisão, mas não quebre a sintaxe nativa do Obsidian.

## Fluxo de Execução (Dois Passes)

A auditoria factual é executada em duas etapas para garantir que correções intermediárias não insiram novas alucinações.

### Etapa 1: Extração de Afirmações e Mapa de Argumentos
1. **Afirmações Checáveis:** Isole cada alegação objetivamente verificável (estatísticas, métricas numéricas, datas, nomes de autores e pesquisadores, atribuições causais, especificações técnicas, resultados de benchmarks e generalizações amplas apresentadas como fatos concretos). Não extraia opiniões puras ou metáforas.
2. **Mapa de Argumentos:** Identifique a tese central do rascunho, quais afirmações factuais sustentam a conclusão (*load-bearing claims*) e quais premissas implícitas foram assumidas.

### Etapa 2: Verificação em Fontes Primárias e Literatura do Cofre (Pass 1)
1. Para cada afirmação extraída:
   - Verifique contra as notas de literatura pertinentes em `zettelbrain/literature/` ou base bruta em `raw/`.
   - Se for alegação empírica externa, pesquise fontes primárias autoritativas via busca web ou bases científicas.
2. Classifique o status de cada afirmação em:
   - `verified`: comprovada por fonte primária ou literatura canônica.
   - `false`: desmentida diretamente por fonte primária ou nota do cofre.
   - `imprecise`: número, ano, versão ou autor materialmente errado.
   - `misleading`: dado isoladamente verdadeiro, mas descontextualizado ou extraído por *cherry-picking*.
   - `unsupported`: ausência de qualquer evidência primária crível que sustente a afirmação.

### Etapa 3: Auditoria Lógica Hostil
Com base no mapa de argumentos, ataque o texto sob a perspectiva de um revisor implacável:
1. **Contradições Internas:** O texto defende uma premissa no início e contradiz essa premissa adiante.
2. **Cherry-Picking:** A evidência apresentada sustenta apenas um recorte restrito, mas o texto deduz uma lei geral.
3. **Premissas Ocultas:** Suposições não declaradas que, se falsas, invalidam a dedução.
4. **Saltos Causais:** Correlação tratada como causa mandatória sem demonstração do mecanismo explicativo.
5. **Omissão Crítica:** Fatos fundamentais omitidos cuja ausência altera radicalmente a validade da afirmação.

### Etapa 4: Relatório de Severidade e Auto-Correção
Apresente os apontamentos ordenados por gravidade decrescente:

| Código | Severidade | Significado | Ação |
| --- | --- | --- | --- |
| **S1** | Falsidade flagrante | Dado inventado, alucinado ou desmentido por fontes primárias | Auto-fix cirúrgico |
| **S2** | Erro material | Número, data, métrica ou nome com valor errado | Auto-fix cirúrgico |
| **S3** | Enganoso / Enquadramento | Dado verdadeiro isoladamente, mas com recorte falacioso | Sugestão e confirmação |
| **S4** | Não suportado | Alegação factual sem fonte primária localizável | Inserir fonte ou enxugar |
| **S5** | Falha de lógica interna | Contradição, salto causal ou premissa inválida | Alerta para autor |
| **S6** | Imprecisão menor | Lapso verbal, imprecisão secundária, arredondamento frouxo | Auto-fix cirúrgico |

Cada apontamento deve conter:
- **Trecho Citado:** A frase exata do texto.
- **Veredito e Severidade:** Código S1-S6 e justificativa concisa.
- **Evidência:** Link da fonte primária ou nota do cofre com a citação/dado canônico.
- **Correção Proposta:** Redação mínima recomendada.

### Etapa 5: Execução do Auto-Fix e Encaminhamento ao `/humanizer`
1. **Aplicação Automática:** Aplique diretamente no arquivo ou rascunho todas as correções de severidade S1, S2, S4 e S6 que não alterem a tese do autor, preservando rigorosamente o estilo dissertativo contínuo sem introduzir listas ou marcadores.
2. **Pausa para Deal Breakers:** Se houver apontamentos S3 ou S5 que ameacem o argumento central, isole-os em uma seção destacada no chat e pergunte como o autor deseja ajustar a tese.
3. **Pass 2 (Auditoria Pós-Correção):** Realize uma leitura rápida das passagens reescritas para garantir que a correção não introduziu novas imprecisões contextuais.
4. **Encaminhamento Obrigatório ao `/humanizer`:** Todo trecho reescrito pelo auto-fix deve ser imediatamente submetido à camada de polimento do `/humanizer` para validação estilística em PT-BR (limite de 4 frases por parágrafo, burstiness, zero travessões explicativos e eliminação de clichês sintáticos de IA).

### Etapa 6: Gravação e Log
1. Sob demanda, atualize o arquivo no disco. Em pipeline, entregue o texto verificado para a etapa final de gravação da respectiva skill geradora.
2. Registre a operação no `.state/log.md` com cabeçalho **`/fact-check`** e a relação de arquivos checados.
