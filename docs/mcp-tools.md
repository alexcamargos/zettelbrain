# Ferramentas MCP (Model Context Protocol)

O ZettelBrain expõe um servidor local compatível com a especificação [Model Context Protocol (MCP)](https://modelcontextprotocol.io/), implementado em [src/mcp/server.py](../src/mcp/server.py) com a biblioteca `FastMCP`. O servidor provê ferramentas determinísticas para agentes de IA interagirem com o cofre, realizarem buscas híbridas, indexarem vetorialmente notas, inspecionarem PDFs e caches do PageIndex, auditarem a base e ingerirem artigos da web.

## Inicialização e Validação

Para validar o estado operacional do servidor e inspecionar os caminhos configurados sem iniciar o transporte stdio:

```powershell
uv run python src/mcp/server.py --health-json
```

Para iniciar o servidor em modo de escuta stdio (utilizado pelos clientes MCP):

```powershell
uv run zettelbrain-mcp
# ou via alias curto
uv run zb-mcp
```

## Resumo das 22 Ferramentas Registradas

| Ferramenta | Categoria | Parâmetros | Finalidade |
| --- | --- | --- | --- |
| `health` | Diagnóstico | Nenhum | Retorna status geral, caminhos do cofre, provedores ativos e políticas operacionais. |
| `retrieval_health` | Diagnóstico | Nenhum | Informa a disponibilidade e status do motor de busca externo `qmd`. |
| `embedding_health` | Diagnóstico | Nenhum | Informa status do índice semântico local de embeddings em `.state/`. |
| `search_zettelbrain` | Busca | `query: str`, `limit: int = 8` | Busca híbrida primária no cofre (`qmd` com fallback BM25 integrado a embeddings). |
| `semantic_search_zettelbrain` | Busca | `query: str`, `limit: int = 8` | Busca puramente vetorial/semântica no índice local. |
| `suggest_zettelbrain_links` | Busca | `relative_path: str`, `limit: int = 5` | Sugere notas candidatas para ligação semântica, excluindo links já existentes. |
| `get_semantic_bridge` | Descoberta | `min_similarity: float = 0.05`, `max_similarity: float = 0.4` | Encontra pares de notas com distância semântica propícia a conexões interdisciplinares. |
| `index_zettelbrain_embeddings` | Indexação | Nenhum | Reconstrói o índice semântico local (`.state/embeddings_index.json`). |
| `list_zettelbrain_markdown` | Arquivos | Nenhum | Lista recursivamente todos os arquivos Markdown dentro de `zettelbrain/`. |
| `read_zettelbrain_markdown` | Arquivos | `relative_path: str` | Lê com segurança o conteúdo UTF-8 de uma nota em `zettelbrain/`. |
| `write_zettelbrain_markdown` | Arquivos | `relative_path: str`, `content: str` | Cria ou atualiza com segurança o conteúdo de uma nota em `zettelbrain/`. |
| `lint_zettelbrain` | Manutenção | Nenhum | Executa auditoria estática completa (links, órfãos, estilo e auto-correções). |
| `compute_pdf_sha256` | PDFs | `relative_path: str` | Calcula o hash SHA-256 canônico de um PDF em `raw/papers/`. |
| `resolve_pdf` | PDFs | `relative_path: str` | Resolve o `document_id` e verifica se o cache PageIndex já existe. |
| `inspect_pdf_manifest` | PDFs | `source_path: str` | Localiza o manifesto PageIndex associado a um caminho de PDF. |
| `list_pdf_manifests` | PDFs | Nenhum | Lista todos os manifestos de PDFs indexados em `.pageindex/`. |
| `read_pdf_cache` | PDFs | `document_id: str`, `query: str \| None = None`, `limit: int = 5` | Lê o cache estruturado PageIndex (`tree.json`), com suporte a busca interna. |
| `read_pdf_page` | PDFs | `document_id: str`, `page: int` | Retorna o texto extraído de uma página específica indexada no PageIndex. |
| `persist_pdf_cache` | PDFs | `relative_path: str`, `tree_json: str` | Grava o `tree.json` e o `manifest.json` do PageIndex na pasta `.pageindex/<hash>/`. |
| `index_pdf_cache` | PDFs | `relative_path: str` | Executa o indexador configurado (`PAGEINDEX_COMMAND` ou Docling) e persiste o cache. |
| `estimate_pdf_processing` | PDFs | `relative_path: str` | Estima total de páginas, volume de tokens, custos aproximados e tempo de processamento. |
| `ingest_web_article` | Ingestão | `url: str`, `filename: str \| None = None` | Baixa artigo web via `trafilatura` e salva Markdown limpo em `raw/articles/`. |

---

## Detalhamento das Ferramentas por Domínio

### 1. Diagnóstico e Governança do Servidor

#### `health()`
- **Descrição:** Retorna as configurações ativas do servidor, caminhos resolvidos do sistema de arquivos e parâmetros operacionais.
- **Retorno:**
  ```json
  {
    "status": "ok",
    "vault_path": "C:\\WorkspaceHub\\SourceHub\\llm_zettelkasten",
    "zettelkasten_path": "C:\\WorkspaceHub\\SourceHub\\llm_zettelkasten\\zettelbrain",
    "raw_articles_path": "C:\\WorkspaceHub\\SourceHub\\llm_zettelkasten\\raw\\articles",
    "raw_youtube_path": "C:\\WorkspaceHub\\SourceHub\\llm_zettelkasten\\raw\\youtube",
    "youtube_playlist_configured": true,
    "qmd_command": "qmd",
    "pageindex_command_configured": false,
    "embedding_provider": "hashing",
    "embedding_model_name": "nomic-embed-text",
    "embedding_endpoint": "http://localhost:11434/api/embeddings",
    "embedding_index_path": "C:\\WorkspaceHub\\SourceHub\\llm_zettelkasten\\.state\\embeddings_index.json",
    "log_level": "INFO",
    "log_rotation": "10 MB",
    "log_retention": "14 days",
    "article_fetch_max_attempts": 2,
    "article_fetch_retry_delay_seconds": 30,
    "embedding_timeout_seconds": 20,
    "qmd_timeout_seconds": 20,
    "pageindex_timeout_seconds": 120,
    "search_default_limit": 8
  }
  ```

#### `retrieval_health()`
- **Descrição:** Diagnóstica se o utilitário de busca externa `qmd` está disponível no ambiente e no PATH.
- **Retorno:** `{"configured": bool, "available": bool, "command": str, "message": str}`.

#### `embedding_health()`
- **Descrição:** Retorna metadados do índice semântico em disco, data da última indexação, quantidade de documentos indexados e dimensões vetoriais.

---

### 2. Busca, Recuperação e Descoberta Semântica

#### `search_zettelbrain(query: str, limit: int = 8)`
- **Descrição:** Executa a busca híbrida central do sistema.
  - Tenta primeiro o motor `qmd` externo se configurado e com resultados.
  - Se `qmd` não retornar dados ou estiver indisponível, executa BM25 léxico local no cofre.
  - Combina o resultado léxico com a busca semântica vetorial local gerada pelo índice de embeddings.
- **Exemplo de Retorno:**
  ```json
  [
    {
      "path": "literature/artigo-autor-conceito.md",
      "score": 0.87,
      "excerpt": "Trecho da nota com a ocorrência dos termos pesquisados...",
      "engine": "bm25+semantic"
    }
  ]
  ```

#### `semantic_search_zettelbrain(query: str, limit: int = 8)`
- **Descrição:** Consulta diretamente o índice de embeddings em `.state/embeddings_index.json` calculando a similaridade de cosseno vetorial.

#### `suggest_zettelbrain_links(relative_path: str, limit: int = 5)`
- **Descrição:** Analisa a nota indicada por `relative_path`, calcula sua proximidade vetorial contra todas as outras notas do cofre e retorna as notas mais afins que **ainda não foram referenciadas** via wikilinks no texto ou no frontmatter. Essencial para conectar notas e mitigar nós órfãos.

#### `get_semantic_bridge(min_similarity: float = 0.05, max_similarity: float = 0.4)`
- **Descrição:** Identifica um par de notas conceituais no cofre com similaridade vetorial intermediária (não óbvias, mas não totalmente desconexas). Utilizada pela skill `/bridge` para gerar atrito criativo e conexões interdisciplinares.

#### `index_zettelbrain_embeddings()`
- **Descrição:** Varre recursivamente `zettelbrain/literature/` e `zettelbrain/permanent/` (ignorando rascunhos, sínteses e índices para preservar a pureza teórica) e gera o arquivo `.state/embeddings_index.json`. Utiliza o provedor configurado (`hashing` determinístico offline ou `ollama`).

---

### 3. Operações Seguras de Leitura e Escrita

Todas as operações de manipulação de arquivos do cofre realizam resolução canônica de caminhos com validação anti-*path traversal*. Tentativas de acessar arquivos fora de `zettelbrain/` são rejeitadas com erro explícito.

#### `list_zettelbrain_markdown()`
- **Descrição:** Lista todos os caminhos relativos de notas Markdown contidas no diretório `zettelbrain/`.

#### `read_zettelbrain_markdown(relative_path: str)`
- **Descrição:** Lê o conteúdo em texto puro de uma nota. `relative_path` deve ser relativo a `zettelbrain/` (ex: `literature/artigo-exemplo.md` ou `permanent/conceito-chave.md`).

#### `write_zettelbrain_markdown(relative_path: str, content: str)`
- **Descrição:** Cria ou sobrescreve uma nota dentro de `zettelbrain/`. Garante a criação de diretórios pais caso ainda não existam.

---

### 4. Auditoria e Linter do Cofre

#### `lint_zettelbrain()`
- **Descrição:** Invoca o motor de análise estática [src/zettelbrain_lint.py](../src/zettelbrain_lint.py).
- **Ações Realizadas:**
  1. Aplica auto-correções determinísticas de nomenclatura em notas de literatura informal (`youtube-[autor]-[titulo].md` e `article-[titulo].md`), reescrevendo todos os wikilinks apontados para o nome anterior.
  2. Normaliza fontes no frontmatter de notas permanentes para o padrão Obsidian (`sources: ["[[nota]]"]`).
  3. Detecta links mortos (`dead_link`).
  4. Identifica notas órfãs (`orphan_note`) e notas com conexão fraca (`weak_connection` < 2 links).
  5. Audita referências a notas marcadas como depreciadas (`deprecated: true`).
  6. Valida regras de estilo em notas conceituais ativas: título H1 obrigatório (`missing_h1_title`), proibição de bullet points no corpo (`style_bullet_points`), proibição de travessões explicativos (`style_em_dash`) e detecção de clichês de IA (`style_ai_cliche`).
  7. Mapeia padrões emergentes: termos em negrito presentes em 3 ou mais notas distintas que ainda não possuem nota permanente dedicada.

---

### 5. Suporte a PDFs Formais e PageIndex

Todas as ferramentas de PDF exigem que o arquivo resida obrigatoriamente dentro de `raw/papers/`.

#### `compute_pdf_sha256(relative_path: str)`
- **Descrição:** Calcula o hash SHA-256 canônico em minúsculas (64 caracteres) do arquivo binário completo do PDF. O hash é o `document_id` exigido pelo PageIndex.

#### `resolve_pdf(relative_path: str)`
- **Descrição:** Calcula o SHA-256 do arquivo e verifica se já existe cache correspondente em `.pageindex/<document_id>/`. Retorna o `document_id`, existência do cache e conteúdo do manifesto se disponível.

#### `read_pdf_cache(document_id: str, query: str | None = None, limit: int = 5)`
- **Descrição:** Lê a árvore estruturada `tree.json` e o `manifest.json` da subpasta `.pageindex/<document_id>/`. Se fornecido `query`, pesquisa os nós da árvore com os termos especificados.

#### `read_pdf_page(document_id: str, page: int)`
- **Descrição:** Extrai o texto correspondente a uma página específica (1-indexed) com base na estrutura de nós indexada no PageIndex.

#### `persist_pdf_cache(relative_path: str, tree_json: str)`
- **Descrição:** Cria a subpasta `.pageindex/<document_id>/`, grava o `tree.json` fornecido e gera automaticamente o `manifest.json` com metadados de tamanho, data UTC e caminho do arquivo de origem.

#### `index_pdf_cache(relative_path: str)`
- **Descrição:** Invoca o comando externo configurado em `PAGEINDEX_COMMAND` ou a biblioteca Docling (se disponível no ambiente) para processar o PDF e materializar a estrutura PageIndex em disco.

#### `estimate_pdf_processing(relative_path: str)`
- **Descrição:** Inspeciona o arquivo PDF e estima total de páginas, volume de tokens, tempo estimado de processamento e projeção de custo para chamadas de LLM.

#### `inspect_pdf_manifest(source_path: str)` e `list_pdf_manifests()`
- **Descrição:** Permitem localizar e listar os manifestos de todos os documentos já processados e armazenados em `.pageindex/`.

---

### 6. Ingestão Automatizada da Web

#### `ingest_web_article(url: str, filename: str | None = None)`
- **Descrição:** Realiza o download do conteúdo textual limpo de uma URL utilizando a biblioteca `trafilatura`. Salva o arquivo em `raw/articles/` com metadados YAML de cabeçalho (URL de origem, data de recuperação, título extraído).
- **Retorno:** `{"status": "success", "output_path": "raw/articles/nome-do-arquivo.md"}` ou mensagem de erro estruturada.

---

## Configuração de Clientes MCP

### Antigravity CLI (`agy`)
O comando `uv run install antigravity` (ou `uv run install agy`) gera o arquivo `mcp_config.json` na raiz do projeto e em `.agents/mcp_config.json`:

```json
{
  "mcpServers": {
    "ZettelBrain": {
      "command": "uv",
      "args": ["run", "src/mcp/server.py"],
      "timeout": 600000
    }
  }
}
```

### Cursor IDE
O comando `uv run install cursor` registra o servidor em `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "ZettelBrain": {
      "command": "uv",
      "args": ["run", "src/mcp/server.py"]
    }
  }
}
```

### Gemini CLI
O comando `uv run install gemini` gera a configuração em `.gemini/settings.json`, mantendo sincronizadas as pastas `.gemini/skills/` e `.agents/skills/`.
