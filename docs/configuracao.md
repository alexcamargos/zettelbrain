# Configuracao e Operacao Local

## Instalacao

```powershell
uv sync
uv run install bootstrap
Copy-Item .env.example .env
uv run python src/mcp/server.py --health-json
```

`uv sync` instala dependencias declaradas em `pyproject.toml` e usa `uv.lock` para reprodutibilidade.
`uv run install bootstrap` cria os diretorios locais de trabalho, como `raw/`, `zettelbrain/`, `logs/`, `.state/` e `.pageindex/`. Em `.state/`, os arquivos `hot.md` e `log.md` podem ser versionados como estado operacional inicial; caches e historicos gerados sao ignorados pelo Git.

## Bootstrap local

Como `raw/`, `zettelbrain/` e `logs/` nao sao rastreados pelo Git, e `.state/` tambem pode precisar de arquivos gerados localmente, um clone novo deve recriar a estrutura de trabalho. Use:

```powershell
uv run install bootstrap
```

Alias equivalente:

```powershell
uv run install local
```

O comando cria, sem adicionar conteudo ao Git:

- `raw/articles/`
- `raw/assets/`
- `raw/papers/`
- `raw/youtube/`
- `zettelbrain/assets/`
- `zettelbrain/drafts/`
- `zettelbrain/literature/`
- `zettelbrain/permanent/`
- `zettelbrain/presentations/`
- `zettelbrain/syntheses/`
- `zettelbrain/visual/`
- `logs/`
- `.state/`
- `.pageindex/`

Arquivos gerados como `.state/historico_ingestao.txt` e `.state/embeddings_index.json` continuam ignorados pelo Git. Os arquivos `.state/hot.md` e `.state/log.md`, quando rastreados, representam o estado operacional versionado do cofre.

## Variaveis de ambiente

As variaveis sao carregadas de `.env` quando o arquivo existe. `.env.example` documenta os defaults.

| Variavel | Default | Uso |
| --- | --- | --- |
| `OBSIDIAN_VAULT_PATH` | `.` | Raiz do cofre/repositorio. |
| `HISTORICO_INGESTAO_PATH` | `.state/historico_ingestao.txt` | Historico de videos YouTube processados. |
| `RAW_ARTICLES_PATH` | `raw/articles` | Artigos web brutos. |
| `RAW_YOUTUBE_PATH` | `raw/youtube` | Transcricoes YouTube brutas. |
| `RAW_PAPERS_PATH` | `raw/papers` | PDFs formais. |
| `ZETTELKASTEN_PATH` | `zettelbrain` | Raiz das notas do cofre. |
| `LOGS_PATH` | `logs` | Logs locais do motor Python. |
| `YOUTUBE_PLAYLIST_ID` | exemplo em `.env.example` | Playlist usada pelo ETL de YouTube. |
| `QMD_COMMAND` | `qmd` | Comando opcional para busca externa. |
| `PAGEINDEX_COMMAND` | vazio | Comando opcional de indexacao PageIndex/PDF. |
| `LLM_MODEL_NAME` | `gemini-2.5-pro` | Nome de modelo usado por fluxos de agente. |
| `EMBEDDING_PROVIDER` | `hashing` | `hashing` ou `ollama`. |
| `EMBEDDING_MODEL_NAME` | `nomic-embed-text` | Modelo de embedding. |
| `EMBEDDING_ENDPOINT` | `http://localhost:11434/api/embeddings` | Endpoint Ollama. |
| `EMBEDDING_INDEX_PATH` | `.state/embeddings_index.json` | Cache de embeddings. |
| `EMBEDDING_DIMENSIONS` | `256` | Dimensoes do embedding hashing. |

## Validacoes

Health check do MCP:

```powershell
uv run python src/mcp/server.py --health-json
```

Linter textual:

```powershell
uv run zettelbrain-lint
```

Linter JSON:

```powershell
uv run zettelbrain-lint --json
```

Para auditar sem aplicar a correcao automatica dos nomes de notas de literatura:

```powershell
uv run zettelbrain-lint --no-fix
```

Testes:

```powershell
uv run pytest
```

## Configurar clientes

Gemini CLI:

```powershell
uv run install gemini
```

Esse comando cria `.gemini/settings.json`, sincroniza `skills/` para `.gemini/skills/` e desativa `.cursorrules` existente renomeando para `.cursorrules.bak`.

Cursor:

```powershell
uv run install cursor
```

Esse comando cria `.cursor/mcp.json` e compila [ZETTELBRAIN.md](../ZETTELBRAIN.md) com todos os arquivos de `skills/` em `.cursorrules`.

Limpeza:

```powershell
uv run install clean
```

Remove `.gemini/`, `.cursor/`, `.cursorrules` e `.cursorrules.bak`.

## ETL de artigos web

```powershell
uv run zb-article-etl --url "https://exemplo.com/artigo"
uv run zb-article-etl --url "https://exemplo.com/artigo" --filename "meu-artigo.md"
```

A saida fica em `raw/articles/` e deve ser processada por `/ingest-article` antes de entrar em `zettelbrain/`.

## ETL de YouTube

```powershell
uv run zb-youtube-etl --dry-run
uv run zb-youtube-etl --limit 5
```

A saida fica em `raw/youtube/` e deve ser processada por `/ingest-youtube`.

## Embeddings

Fallback offline deterministico:

```powershell
$env:EMBEDDING_PROVIDER="hashing"
uv run python src/mcp/server.py --health-json
```

Ollama local:

```powershell
$env:EMBEDDING_PROVIDER="ollama"
$env:EMBEDDING_MODEL_NAME="nomic-embed-text"
$env:EMBEDDING_ENDPOINT="http://localhost:11434/api/embeddings"
```

Se o endpoint Ollama falhar, a implementacao cai para hashing.
