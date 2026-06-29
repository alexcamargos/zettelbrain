# Ferramentas MCP

O servidor MCP e implementado em [../src/mcp/server.py](../src/mcp/server.py). Execute health check com:

```powershell
uv run python src/mcp/server.py --health-json
```

Inicie o servidor com:

```powershell
uv run zettelbrain-mcp
```

## Ferramentas registradas

| Ferramenta | Finalidade |
| --- | --- |
| `health` | Retorna status, caminhos configurados e provedores ativos. |
| `search_zettelbrain` | Busca hibrida no cofre por `qmd`, BM25 e embeddings. |
| `retrieval_health` | Informa se `qmd` esta configurado e disponivel. |
| `embedding_health` | Informa status do indice de embeddings. |
| `index_zettelbrain_embeddings` | Recria `.state/embeddings_index.json`. |
| `semantic_search_zettelbrain` | Busca semantica usando indice local. |
| `list_zettelbrain_markdown` | Lista Markdown dentro de `zettelbrain/`. |
| `get_semantic_bridge` | Encontra par de notas com distancia semantica util. |
| `read_zettelbrain_markdown` | Le Markdown do cofre com limite de path seguro. |
| `write_zettelbrain_markdown` | Cria ou edita Markdown dentro de `zettelbrain/` com limite de path seguro. |
| `lint_zettelbrain` | Executa linter de integridade do cofre. |
| `inspect_pdf_manifest` | Localiza manifest PageIndex por PDF de origem. |
| `list_pdf_manifests` | Lista manifests PageIndex existentes. |
| `read_pdf_cache` | Le cache PageIndex por `document_id`, com busca opcional. |
| `resolve_pdf` | Calcula SHA-256 de PDF em `raw/papers/` e verifica cache. |
| `read_pdf_page` | Retorna texto de uma pagina especifica do cache. |
| `persist_pdf_cache` | Persiste `tree.json` e `manifest.json` para um PDF. |
| `index_pdf_cache` | Roda comando externo ou Docling para indexar PDF. |
| `compute_pdf_sha256` | Calcula SHA-256 de PDF dentro de `raw/papers/`. |
| `estimate_pdf_processing` | Estima paginas, tokens, custos e tempo de processamento. |
| `ingest_web_article` | Baixa artigo web e salva em `raw/articles/`. |

## Contratos importantes

- Ferramentas de PDF aceitam apenas arquivos dentro de `raw/papers/`.
- `document_id` deve ser SHA-256 em minusculas com 64 caracteres.
- Leitura e escrita de Markdown sao limitadas ao diretorio `zettelbrain/`.
- `index_zettelbrain_embeddings` indexa apenas `zettelbrain/literature/` e `zettelbrain/permanent/`.
- `EMBEDDING_PROVIDER` aceita `hashing` e `ollama`.
- `QMD_COMMAND` e opcional; quando ausente ou indisponivel, a busca local usa BM25.

## Exemplo de configuracao MCP gerada

`uv run install gemini` gera uma configuracao equivalente a:

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

`uv run install cursor` gera configuracao equivalente em `.cursor/mcp.json`, sem o campo `timeout`.
