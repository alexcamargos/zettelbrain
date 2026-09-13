# Arquitetura e Estrutura do Projeto

## Visao geral

ZettelBrain e composto por um cofre Markdown, um conjunto de workflows textuais para agentes e um motor Python local. O motor Python nao substitui as skills: ele fornece ferramentas deterministicas para tarefas que nao devem depender de leitura livre do modelo, como lint, busca, hash de PDF, cache PageIndex e ETLs.

## Estrutura atual

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
|   |-- logger.py
|   |-- setup.py
|   |-- utils.py
|   |-- zettelbrain_lint.py
|   |-- zettelbrain_mcp.py
|   |-- ingestion/
|   |   |-- article_etl.py
|   |   `-- youtube_etl.py
|   `-- mcp/
|       |-- server.py
|       |-- tools_command.py
|       |-- tools_embeddings.py
|       |-- tools_file.py
|       |-- tools_pdf.py
|       `-- tools_search.py
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

## Modulos Python

| Modulo | Papel |
| --- | --- |
| `src/config.py` | Carrega `.env`, resolve caminhos, valida configuracao e centraliza politicas operacionais (logging, retries, timeouts e limites). |
| `src/logger.py` | Configura logs estruturados com loguru ou fallback stdlib e decorador de execucao de ferramentas. |
| `src/setup.py` | Gera configuracoes locais para Gemini CLI e Cursor. |
| `src/utils.py` | Funcoes utilitarias comuns, como geracao deterministica de slugs seguros. |
| `src/zettelbrain_lint.py` | Audita integridade do cofre. |
| `src/zettelbrain_mcp.py` | Bootstrap do servidor MCP. |
| `src/ingestion/article_etl.py` | Baixa e limpa artigos web com `trafilatura`. |
| `src/ingestion/youtube_etl.py` | Lê RSS de playlist YouTube e grava transcricoes. |
| `src/mcp/server.py` | Registra ferramentas MCP com FastMCP. |
| `src/mcp/tools_search.py` | Busca BM25 local e integracao opcional com `qmd`. |
| `src/mcp/tools_embeddings.py` | Indice semantico local por hashing ou Ollama. |
| `src/mcp/tools_pdf.py` | Hash SHA-256, cache PageIndex e leitura de PDF indexado. |
| `src/mcp/tools_file.py` | Listagem e leitura segura de Markdown do cofre. |
| `src/mcp/tools_command.py` | Split seguro de comandos configuraveis. |

## Modelo de dados do cofre

O cofre usa Markdown com frontmatter YAML. Apenas notas em `zettelbrain/literature/` e `zettelbrain/permanent/` entram no indice semantico local de embeddings. Rascunhos, overview e indice raiz ficam fora desse indice por decisao implementada em `tools_embeddings.py`.

## Busca e recuperacao

`search_zettelbrain` usa uma estrategia hibrida:

1. tenta `qmd` quando `QMD_COMMAND` esta configurado e disponivel;
2. usa BM25 local quando `qmd` nao retorna resultado;
3. mescla busca primaria com busca semantica local quando aplicavel.

O indice semantico local e gravado em `.state/embeddings_index.json`.

## PDFs e PageIndex

PDFs devem ficar em `raw/papers/`. O `document_id` e sempre o SHA-256 do binario completo. O cache fica em `.pageindex/<document_id>/tree.json` e `.pageindex/<document_id>/manifest.json`.

O modulo `tools_pdf.py` aceita:

- persistencia de arvore PageIndex recebida como JSON;
- indexacao por comando externo configurado em `PAGEINDEX_COMMAND`;
- indexacao por Docling quando o pacote estiver instalado e selecionado;
- estimativa de paginas, tokens, custo e tempo.

## Configuracoes de cliente

`ZETTELBRAIN.md` e `skills/` sao fontes canonicas operacionais. Arquivos `.gemini/`, `.cursor/` e `.cursorrules` sao configuracoes locais geradas por `src/setup.py`.

Como `raw/`, `zettelbrain/` e `logs/` sao ignorados pelo Git, clones novos devem executar `uv run install bootstrap` para criar a estrutura local de trabalho.

## Testes

A suite cobre configuracao, ETLs, busca, leitura segura de arquivos, embeddings, cache PageIndex, linter e setup de clientes. Execute:

```powershell
uv run pytest
```
