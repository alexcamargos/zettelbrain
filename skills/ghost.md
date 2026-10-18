# /ghost (Redação Acadêmica e Síntese Textual)

## Objetivo
Atuar como um assistente de redação acadêmica avançada. O foco é minerar o conhecimento validado no ZettelBrain, debater ativamente a estrutura do texto com o usuário e redigir rascunhos de alta densidade técnica para capítulos de dissertações ou artigos estruturados. Todo o material gerado deve ser salvo isoladamente no diretório `zettelbrain/drafts/`.

## Gatilho
Acionado quando o usuário disser `gemini "Execute a skill /ghost para escrever sobre [tópico]"` ou `/ghost [tópico]`

**Log:** Ao acrescentar entradas em `.state/log.md`, use estritamente o formato definido no `ZETTELBRAIN.md` (seção Convenção do log operacional). No cabeçalho use **`/ghost`**. No corpo liste **todos** os caminhos relativos de arquivos criados ou alterados e das notas lidas como base (enumerando cada caminho).

## Fluxo de Execução (Workflow)

### Etapa 1: Mineração e Escopo Inicial
1. Priorize `ZettelBrain.search_zettelbrain` para localizar Notas Permanentes e Notas de Literatura relevantes ao tópico solicitado por busca híbrida ou fallback lexical local.
2. Use `ZettelBrain.read_zettelbrain_markdown` para ler o conteúdo das notas candidatas retornadas. Se o MCP estiver indisponível ou insuficiente, acesse `zettelbrain/index.md` e localize manualmente todas as notas relevantes.
3. Leia o conteúdo destas notas para compreender o panorama teórico, os dados estatísticos disponíveis e as divergências entre autores. Quando houver referência a PDF e cache PageIndex, use `ZettelBrain.resolve_pdf`, `ZettelBrain.read_pdf_cache` ou `ZettelBrain.read_pdf_page` apenas como apoio de navegação e confirmação localizada, sem substituir as notas do cofre como fonte primária.

### Etapa 2: Alinhamento Estratégico (Pausa Obrigatória e Interação)
É terminantemente proibido iniciar a redação do texto antes de concluir esta etapa. Apresente ao usuário um plano de voo contendo:
1. **Notas Selecionadas:** A lista das notas que serão utilizadas como base (com seus respectivos links).
2. **Proposta de Tese:** Qual será o argumento central ou a conclusão lógica deste rascunho.
3. **Esqueleto do Texto:** A progressão de argumentos e blocos temáticos que serão desenvolvidos ao longo do rascunho, dimensionados conforme a complexidade do tema.
4. **Interação Exigida:** Pergunte explicitamente ao usuário:
   a) "Devemos incluir ou excluir alguma nota específica desta seleção?"
   b) "A proposta de tese está alinhada com seu objetivo ou devemos focar em outro ângulo analítico?"
   c) "Existe alguma variável, algoritmo ou métrica que exige destaque obrigatório neste texto?"
5. Aguarde o retorno detalhado do usuário e refine o esqueleto até obter a aprovação final.

### Etapa 3: Execução da Escrita (Aplicação Rigorosa de Estilo)
Somente após a aprovação do plano pelo usuário, inicie a redação. O texto gerado DEVE obedecer de forma inegociável às **Regras Globais de Estilo**:
- É terminantemente proibido o uso de listas ou marcadores (bullet points).
- Desenvolva a redação em parágrafos contínuos e articulados de prosa, sem gravar rótulos artificiais de seção no corpo do texto e sem impor um número fixo de parágrafos, apresentando o problema ou conceito acadêmico, desenvolvendo as evidências, cruzando dados, citando autores e metodologias, e discutindo as implicações para o modelo estudado.
- Aplique a **Técnica Feynman** adaptada para um público de nível executivo e pós-graduação. Simplifique a complexidade matemática ou estatística preservando o rigor técnico.
- Aplique **negrito** exclusivamente para destacar constructos teóricos, variáveis de modelo e termos técnicos centrais.
- Não utilize travessões. A fluidez explicativa deve ser construída com vírgulas e períodos diretos.
- Não utilize emojis.
- Todo dado ou conceito extraído de uma nota deve ser referenciado ao longo do texto utilizando o wikilink correspondente (ex: `[[nome-da-nota]]`). Quando aplicável, inclua a citação ABNT no corpo do texto.
- Aplique obrigatoriamente a camada de auditoria factual da skill `/fact-check`: extraia as afirmações checáveis, valide contra as notas de literatura de origem e fontes primárias, aplicando auto-correção (auto-fix) em erros objetivos (S1, S2, S4, S6) e submetendo eventuais deal breakers lógicos (S3, S5) à aprovação do usuário.
- Aplique obrigatoriamente a camada de polimento da skill `/humanizer`: passe o texto pelos 8 testes de auto-auditoria, eliminando clichês de LLM, falsos contrastes ("Não é X, é Y"), gerúndios vazios de cauda e tríades forçadas, respeitando o teto de 4 frases por parágrafo e variando a cadência (burstiness) para máxima legibilidade humana, sem recorrer à oralidade informal.

### Etapa 4: Salvamento e Indexação
1. Salve o rascunho completo em um novo arquivo no diretório `zettelbrain/drafts/rascunho-[tópico].md`.
2. Adicione o link semântico do novo rascunho ao arquivo `zettelbrain/index.md` na seção correspondente a rascunhos em andamento.
3. Atualize o arquivo `.state/log.md` com cabeçalho **`/ghost`**, caminho do rascunho criado, alterações em `zettelbrain/index.md` se houver, e **lista explícita** de cada nota de fonte lida em profundidade.
