# /start (Briefing e Inicialização de Sessão)

## Objetivo
Preparar o ambiente de trabalho e situar o usuário no início de uma nova sessão de estudo ou pesquisa. Esta skill recupera o contexto imediato da base de conhecimento, permitindo uma transição suave para as atividades produtivas sem necessidade de revisão manual de arquivos.

## Gatilho
Acionado quando o usuário disser `gemini "Execute a skill /start"` ou `gemini "Inicie a sessão"` ou `/start`

**Log:** Esta skill não grava em `.state/log.md`. Skills que registrarem operações devem seguir o formato do `ZETTELBRAIN.md` (seção Convenção do log operacional).

## Fluxo de Execução (Workflow)

### Etapa 1: Recuperação de Contexto Recente
1. Acesse e leia o arquivo `.state/hot.md` para absorver o foco atual, as questões em aberto e as decisões mais recentes da última sessão.
2. Leia as últimas 5 entradas do arquivo `.state/log.md` para compreender o volume e o tipo de operações realizadas recentemente.
3. Leia `zettelbrain/overview.md` quando existir, para alinhar o briefing com a síntese viva do cofre (última regeneração típica via `/lint`).
4. Se as últimas entradas de `.state/log.md` mencionarem caminhos sob `.pageindex/`, incorpore no briefing (em prosa, sem listas) que há **índice PageIndex** associado aos PDFs indicados, sem carregar o `tree.json` completo na resposta.

### Etapa 2: Elaboração do Briefing de Abertura (Aplicação Rigorosa de Estilo)
Gere um resumo de situação para o usuário. A redação deste texto DEVE obedecer integralmente às **Regras Globais de Estilo**:
- É terminantemente proibido o uso de listas ou marcadores (bullet points).
- Desenvolva o briefing em parágrafos contínuos de prosa concisa, sem gravar rótulos artificiais de seção no corpo do texto, apresentando o estado atual da pesquisa, recapitulando as decisões críticas tomadas e as questões pendentes, e sugerindo diretamente o próximo passo lógico ou fonte a ser processada.
- Aplique o tom analítico adequado para um profissional sênior e estudante de MBA, utilizando a lógica evolutiva de conhecimento.
- Utilize **negrito** exclusivamente para destacar o foco de estudo, conceitos centrais ou nomes de arquivos cruciais para a sessão atual.
- Não utilize travessões; garanta a fluidez da explicação através de vírgulas e períodos curtos.
- Não utilize emojis.

### Etapa 3: Prontidão Operacional
1. Informe ao usuário que o sistema está pronto para receber comandos de ingestão, busca ou redação.
2. Não realize qualquer alteração em arquivos nesta etapa; o objetivo é apenas o alinhamento de contexto.
