# ZettelBrain

[![Python](https://img.shields.io/badge/python-%3E%3D3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![uv](https://img.shields.io/badge/package%20manager-uv-261230)](https://github.com/astral-sh/uv)
[![Obsidian](https://img.shields.io/badge/visual%20vault-Obsidian-7C3AED?logo=obsidian&logoColor=white)](https://obsidian.md/)
[![Zettelkasten](https://img.shields.io/badge/knowledge%20base-Zettelkasten-2f855a)](zettelbrain/index.md)
[![Markdown](https://img.shields.io/badge/notes-Markdown-000000?logo=markdown&logoColor=white)](zettelbrain/)
[![MCP](https://img.shields.io/badge/agent%20tools-MCP-6f42c1)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/github/license/alexcamargos/llm_zettelkasten)](LICENSE)

ZettelBrain e um cofre Zettelkasten em Markdown com um motor Python local para automacao, busca, ingestao e exposicao de ferramentas via Model Context Protocol (MCP).

O projeto combina tres superficies:

- `zettelbrain/`: cofre de conhecimento, com notas de literatura, permanentes, rascunhos, sinteses, visualizacoes e indice.
- `skills/`: fluxos operacionais usados por agentes para ingestao, busca, manutencao e escrita.
- `src/`: motor Python com configuracao, ETLs, linter, busca, embeddings, cache PageIndex/PDF e servidor MCP.

## Referencias do projeto

Arquivo operacional base:

- [Schema operacional do ZettelBrain](ZETTELBRAIN.md)

Documentacao de consulta para terceiros:

- [Manual de funcionalidades e skills](docs/manual-funcionalidades-agente.md)
- [Arquitetura e estrutura do projeto](docs/arquitetura.md)
- [Configuracao e operacao local](docs/configuracao.md)
- [Ferramentas MCP](docs/mcp-tools.md)
- [Auditoria de alinhamento da documentacao](docs/auditoria-documentacao.md)

## Inicio rapido

Requisitos principais:

- Python `>=3.12`
- `uv`
- Opcional: `qmd` para busca semantica externa
- Opcional: Ollama local para embeddings com `EMBEDDING_PROVIDER=ollama`
- Opcional: comando PageIndex ou Docling para indexacao de PDFs

Prepare o ambiente:

```powershell
uv sync
uv run install bootstrap
Copy-Item .env.example .env
uv run python src/mcp/server.py --health-json
```

Execute verificacoes locais:

```powershell
uv run zettelbrain-lint
uv run zettelbrain-lint --json
uv run pytest
```

Configure um cliente de agente quando necessario:

```powershell
uv run install gemini
uv run install cursor
uv run install clean
```

`uv run install gemini` cria `.gemini/settings.json` e sincroniza `skills/` para `.gemini/skills/`. `uv run install cursor` cria `.cursor/mcp.json` e compila `ZETTELBRAIN.md` com `skills/` em `.cursorrules`.

## Comandos de uso comum

| Objetivo | Comando |
| --- | --- |
| Validar servidor MCP sem iniciar transporte | `uv run python src/mcp/server.py --health-json` |
| Iniciar servidor MCP | `uv run zettelbrain-mcp` ou `uv run zb-mcp` |
| Rodar linter do cofre | `uv run zettelbrain-lint` ou `uv run zb-lint` |
| Gerar JSON do linter | `uv run zettelbrain-lint --json` |
| Baixar artigo web para `raw/articles/` | `uv run zb-article-etl --url "<URL>"` |
| Ingerir transcricoes novas de playlist YouTube | `uv run zb-youtube-etl --limit 5` |
| Ver candidatos YouTube sem escrever arquivos | `uv run zb-youtube-etl --dry-run` |
| Criar estrutura local ignorada pelo Git | `uv run install bootstrap` ou `uv run install local` |
| Configurar Gemini CLI | `uv run install gemini` |
| Configurar Cursor | `uv run install cursor` |
| Remover configuracoes locais de cliente | `uv run install clean` |

## Estrutura principal

```text
.
|-- README.md
|-- LICENSE
|-- pyproject.toml
|-- uv.lock
|-- docs/
|-- skills/
|-- src/
|   |-- config.py
|   |-- setup.py
|   |-- zettelbrain_lint.py
|   |-- zettelbrain_mcp.py
|   |-- ingestion/
|   `-- mcp/
|-- tests/
|-- raw/
|   |-- articles/
|   |-- papers/
|   |-- youtube/
|   `-- assets/
|-- zettelbrain/
|   |-- index.md
|   |-- overview.md
|   |-- literature/
|   |-- permanent/
|   |-- drafts/
|   |-- syntheses/
|   |-- visual/
|   |-- presentations/
|   `-- assets/
|-- .state/
`-- .pageindex/
```

## Estado dos artefatos locais

Arquivos gerados localmente, caches, logs, `.env`, ambientes virtuais, fontes brutas em `raw/` e notas de trabalho em `zettelbrain/` sao ignorados pelo Git. Em `.state/`, caches e historicos gerados sao ignorados, enquanto `hot.md` e `log.md` podem ser rastreados como estado operacional inicial. Em clones novos, rode `uv run install bootstrap` para criar a estrutura local.

## Licenca

Consulte [LICENSE](LICENSE).
