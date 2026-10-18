# Guia de Configuração e Operação Local

Este documento orienta a configuração do ambiente de desenvolvimento, parametrização de variáveis, configuração de clientes de IA e operação dos utilitários CLI do **ZettelBrain**.

---

## 1. Requisitos do Sistema e Instalação

### Pré-requisitos
- **Python**: Versão `>=3.12`.
- **Gerenciador de Pacotes**: [Astral uv](https://github.com/astral-sh/uv) (obrigatório para resolução determinística de dependências).
- **Opcionais**:
  - [Ollama](https://ollama.ai/) local: Para geração de embeddings neurais caso utilize `EMBEDDING_PROVIDER=ollama`.
  - Utilitário `qmd`: Para busca externa indexada caso utilize `QMD_COMMAND`.
  - Ferramenta [PageIndex MCP](https://github.com/VectifyAI/pageindex-mcp) ou Docling: Para indexação automática de PDFs em `raw/papers/`.

### Passo a Passo de Instalação

1. Clone o repositório e navegue até a raiz:
   ```powershell
   git clone https://github.com/alexcamargos/llm_zettelkasten.git
   cd llm_zettelkasten
   ```

2. Sincronize o ambiente virtual e as dependências travadas no `uv.lock`:
   ```powershell
   uv sync
   ```

3. Crie a malha de diretórios de trabalho locais:
   ```powershell
   uv run install bootstrap
   ```

4. Crie o arquivo `.env` a partir do template:
   ```powershell
   Copy-Item .env.example .env
   ```

5. Valide a integridade do ambiente com o health check do servidor MCP:
   ```powershell
   uv run python src/mcp/server.py --health-json
   ```

---

## 2. Bootstrap da Estrutura Local de Trabalho

Por razões de privacidade, controle de versão e tamanho de binários, os diretórios contendo fontes brutas (`raw/`), notas do cofre (`zettelbrain/`), logs (`logs/`), árvores indexadas (`.pageindex/`) e caches gerados (`.state/embeddings_index.json`, `.state/historico_ingestao.txt`) **não são rastreados pelo Git**.

Ao clonar o repositório em uma nova máquina, execute:

```powershell
uv run install bootstrap
# ou o alias equivalente
uv run install local
```

Este comando cria automaticamente, caso não existam:
- `raw/articles/`, `raw/papers/`, `raw/youtube/`, `raw/assets/`
- `zettelbrain/literature/`, `zettelbrain/permanent/`, `zettelbrain/drafts/`, `zettelbrain/syntheses/`, `zettelbrain/visual/`, `zettelbrain/presentations/`, `zettelbrain/assets/`
- `logs/`
- `.state/`
- `.pageindex/`

> **Nota sobre o estado operacional**: Os arquivos `.state/hot.md` e `.state/log.md` podem ser rastreados no controle de versão para manter o diário operacional do cofre. Apenas os arquivos de cache e histórico gerados dentro de `.state/` são ignorados.

---

## 3. Guia de Variáveis de Ambiente (`.env`)

O motor Python carrega as variáveis definidas no arquivo `.env` localizado na raiz do repositório através de `pydantic-settings`.

### Tabela Completa de Parâmetros

| Variável | Padrão (Default) | Descrição e Finalidade |
| --- | --- | --- |
| **Caminhos e Diretórios** | | |
| `OBSIDIAN_VAULT_PATH` | `.` | Raiz do repositório/cofre. Todos os caminhos relativos são resolvidos a partir daqui. |
| `ZETTELKASTEN_PATH` | `zettelbrain` | Diretório onde residem as notas Markdown do cofre. |
| `RAW_ARTICLES_PATH` | `raw/articles` | Diretório de destino para artigos web brutos baixados. |
| `RAW_PAPERS_PATH` | `raw/papers` | Diretório de entrada obrigatório para PDFs e artigos formais. |
| `RAW_YOUTUBE_PATH` | `raw/youtube` | Diretório de destino para transcrições brutas do YouTube. |
| `LOGS_PATH` | `logs` | Diretório de armazenamento dos logs do motor Python. |
| `HISTORICO_INGESTAO_PATH` | `.state/historico_ingestao.txt` | Arquivo que armazena IDs de vídeos do YouTube já ingeridos para evitar duplicatas. |
| **Modelos de IA** | | |
| `LLM_MODEL_NAME` | `gemini-2.5-pro` | Nome do modelo de linguagem de referência para os agentes. |
| **Embeddings e Busca Vetorial** | | |
| `EMBEDDING_PROVIDER` | `hashing` | Provedor de vetorização. Aceita `hashing` (offline determinístico) ou `ollama` (neural). |
| `EMBEDDING_MODEL_NAME` | `nomic-embed-text` | Nome do modelo neural quando utilizado o provedor `ollama`. |
| `EMBEDDING_ENDPOINT` | `http://localhost:11434/api/embeddings` | URL da API REST do Ollama para geração de vetores. |
| `EMBEDDING_INDEX_PATH` | `.state/embeddings_index.json` | Local onde o cache vetorial gerado pelo MCP é gravado. |
| `EMBEDDING_DIMENSIONS` | `256` | Quantidade de dimensões vetoriais no cálculo de hashing determinístico. |
| `EMBEDDING_TIMEOUT_SECONDS` | `20` | Tempo limite em segundos para requisições ao endpoint de embeddings. |
| **Busca Híbrida e Léxica** | | |
| `QMD_COMMAND` | `qmd` | Comando de terminal para o utilitário de busca externa `qmd` (opcional). |
| `QMD_TIMEOUT_SECONDS` | `20` | Timeout para execução de chamadas ao `qmd`. |
| `SEARCH_DEFAULT_LIMIT` | `8` | Quantidade padrão de resultados retornados pelas buscas no cofre. |
| **PageIndex e PDFs** | | |
| `PAGEINDEX_COMMAND` | `""` (vazio) | Comando de terminal para indexação externa de PDFs via PageIndex CLI. |
| `PAGEINDEX_TIMEOUT_SECONDS` | `120` | Timeout para indexação de PDFs longos. |
| **ETLs de Ingestão** | | |
| `YOUTUBE_PLAYLIST_ID` | Exemplo em `.env.example` | ID da playlist do canal do YouTube utilizada pelo ETL `zb-youtube-etl`. |
| `ARTICLE_FETCH_MAX_ATTEMPTS` | `2` | Número máximo de tentativas de download de um artigo web pelo ETL. |
| `ARTICLE_FETCH_RETRY_DELAY_SECONDS` | `30` | Intervalo em segundos entre tentativas com falha no download de artigo. |
| **Logging e Observabilidade** | | |
| `LOG_LEVEL` | `INFO` | Nível mínimo de severidade do log (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `LOG_ROTATION` | `10 MB` | Tamanho máximo por arquivo antes de rotacionar o log (`loguru`). |
| `LOG_RETENTION` | `14 days` | Período de retenção e descarte de arquivos antigos de log. |

---

## 4. Configuração de Clientes de IA

O utilitário `src/setup.py` gerencia a integração nativa com diferentes clientes de agentes de IA:

### Antigravity CLI (`agy`)
O Antigravity é o ambiente recomendado para agentes autônomos. Execute:

```powershell
uv run install antigravity
# ou via alias curto
uv run install agy
```

**Efeitos do comando**:
1. Cria `.agents/skills/<name>/SKILL.md` para cada uma das 15 skills do cofre.
2. Insere automaticamente o cabeçalho YAML frontmatter (`name` e `description`) permitindo que o CLI do Antigravity (`agy`) reconheça e autocomplete slash commands (ex: `/start`, `/recall`, `/ghost`).
3. Gera `mcp_config.json` na raiz e `.agents/mcp_config.json` configurando o servidor MCP ZettelBrain.
4. Desativa temporariamente eventuais regras do Cursor (`.cursorrules` renomeado para `.cursorrules.bak`) para evitar poluição de contexto.

### Cursor IDE
Para utilizar o ZettelBrain dentro do Cursor IDE:

```powershell
uv run install cursor
```

**Efeitos do comando**:
1. Cria `.cursor/mcp.json` apontando para o servidor FastMCP.
2. Compila as regras mestras de [ZETTELBRAIN.md](../ZETTELBRAIN.md) e o acervo completo de [skills/](../skills/) em um único arquivo consolidado `.cursorrules`.

### Gemini CLI
Para clientes legados do Gemini CLI:

```powershell
uv run install gemini
```

Sincroniza simultaneamente o ambiente Antigravity (`.agents/`) e o diretório `.gemini/` (`settings.json` e `.gemini/skills/`).

### Desinstalação e Limpeza
Para remover todos os arquivos gerados de clientes e desvincular o cofre:

```powershell
uv run install clean
```

Remove com segurança: `.agents/`, `.gemini/`, `.cursor/`, `mcp_config.json`, `.cursorrules` e `.cursorrules.bak`.

---

## 5. Operação dos Comandos e Scripts CLI

O `pyproject.toml` disponibiliza comandos de terminal diretos:

### Linter do Cofre (`zettelbrain-lint` / `zb-lint`)
Audita a integridade referencial, estrutura do grafo e estilo de redação das notas:

```powershell
# Execução padrão (aplica correções automáticas seguras e exibe relatório legível)
uv run zb-lint

# Audita sem modificar arquivos no disco (modo somente leitura)
uv run zb-lint --no-fix

# Retorna o resultado estritamente em JSON estruturado (ideal para pipelines e agentes)
uv run zb-lint --json
```

**Códigos de Saída do Processo**:
- `0`: Cofre íntegro (pode conter avisos não impeditivos como notas órfãs).
- `1`: Erros críticos detectados (ex: links mortos ou falha de parsing YAML).
- `2`: Erro fatal de execução ou exceção de runtime.

### ETL de Artigos Web (`zettelbrain-article-etl` / `zb-article-etl`)
Baixa o conteúdo textual limpo de páginas web e salva em `raw/articles/`:

```powershell
# Download automático gerando slug a partir do título
uv run zb-article-etl --url "https://exemplo.com/artigo-de-pesquisa"

# Download especificando o nome de arquivo de saída
uv run zb-article-etl --url "https://exemplo.com/artigo" --filename "artigo-especifico.md"
```

### ETL de YouTube (`zettelbrain-youtube-etl` / `zb-youtube-etl`)
Processa a playlist configurada em `YOUTUBE_PLAYLIST_ID` e extrai legendas para `raw/youtube/`:

```powershell
# Simulação (exibe vídeos pendentes sem gravar arquivos no disco)
uv run zb-youtube-etl --dry-run

# Ingestão de até 5 vídeos novos pendentes
uv run zb-youtube-etl --limit 5
```

### Servidor MCP (`zettelbrain-mcp` / `zb-mcp`)
Inicia o servidor MCP local para conexão de agentes:

```powershell
uv run zb-mcp
```

---

## 6. Rotinas de Manutenção e Desenvolvimento

### Execução de Testes
O projeto utiliza exclusivamente o **`pytest`** acompanhado do **`pytest-mock`**:

```powershell
# Executa toda a suíte de testes (131+ testes)
uv run pytest

# Executa testes com saída detalhada
uv run pytest -v

# Executa testes de um arquivo específico
uv run pytest tests/test_zettelbrain_lint.py
```

### Análise Estática de Código (Ruff)
O código Python segue estritamente a PEP 8 e tipagem estrita para Python 3.12:

```powershell
# Verifica erros de lint
uv run ruff check

# Aplica correções automáticas seguras
uv run ruff check --fix

# Formata o código
uv run ruff format
```

### Verificação de Logs
Logs operacionais estruturados são registrados em `logs/zettelbrain.log`:

```powershell
Get-Content -Path logs/zettelbrain.log -Tail 50 -Wait
```
