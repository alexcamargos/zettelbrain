"""Model Context Protocol (MCP) server for the LLM ZettelBrain project.

Exposes tools for searching the ZettelBrain vault, listing/reading markdown
files, and reading/writing the PageIndex cache for PDF files.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# ruff: noqa: E402

SRC_ROOT = Path(__file__).resolve().parents[1]
MCP_TOOLS_ROOT = Path(__file__).resolve().parent
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
if str(MCP_TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(MCP_TOOLS_ROOT))

from tools_embeddings import (
    build_embedding_index,
    embedding_status,
    find_semantic_bridge,
    semantic_search,
    suggest_note_links,
)
from tools_file import list_markdown_files, read_markdown_file, write_markdown_file
from tools_pdf import (
    estimate_document_processing,
    find_pageindex_manifest,
    index_pdf_with_command,
    list_pageindex_manifests,
    persist_pageindex_cache,
    read_pageindex_cache,
    read_pageindex_page,
    resolve_pdf_cache,
    sha256_file,
)
from tools_search import SearchResult, hybrid_search, merge_search_results, retrieval_status

from config import load_settings
from ingestion.article_etl import save_raw_article
from logger import configure_logging, log_skill_execution
from zettelbrain_lint import run_lint_logic

settings = load_settings()
configure_logging(settings.logs_path)


@log_skill_execution
def health() -> dict[str, Any]:
    """Retrieve server status and system configuration paths.

    Returns:
        dict[str, Any]: Server status mapping with configuration keys and settings.

    """
    return {
        "status": "ok",
        "vault_path": str(settings.vault_path),
        "zettelkasten_path": str(settings.zettelkasten_path),
        "raw_articles_path": str(settings.raw_articles_path),
        "raw_youtube_path": str(settings.raw_youtube_path),
        "youtube_playlist_configured": bool(settings.youtube_playlist_id),
        "qmd_command": settings.qmd_command,
        "pageindex_command_configured": bool(settings.pageindex_command),
        "embedding_provider": settings.embedding_provider,
        "embedding_model_name": settings.embedding_model_name,
        "embedding_endpoint": settings.embedding_endpoint,
        "embedding_index_path": str(settings.embedding_index_path),
    }


@log_skill_execution
def search_zettelbrain(query: str, limit: int = 8) -> list[dict[str, Any]]:
    """Perform a hybrid (lexical + semantic qmd fallback) search on the ZettelBrain.

    Args:
        query: The search query text term(s).
        limit: The maximum number of search results to return. Defaults to 8.

    Returns:
        list[dict[str, Any]]: List of dictionary mappings representing search results.

    """
    primary_results = hybrid_search(
        settings.zettelkasten_path,
        query,
        limit=limit,
        qmd_command=settings.qmd_command,
    )
    if primary_results and primary_results[0].engine == "qmd":
        results = primary_results
    else:
        semantic_results = semantic_search(
            settings.zettelkasten_path,
            settings.embedding_index_path,
            query,
            limit=limit,
            provider=settings.embedding_provider,
            dimensions=settings.embedding_dimensions,
            model_name=settings.embedding_model_name,
            endpoint=settings.embedding_endpoint,
        )
        results = merge_search_results(
            primary_results,
            [
                SearchResult(
                    path=result.path,
                    score=result.score,
                    excerpt=result.excerpt,
                    engine=result.engine,
                )
                for result in semantic_results
            ],
            limit=limit,
        )
    return [result.__dict__ for result in results]


@log_skill_execution
def retrieval_health() -> dict[str, Any]:
    """Retrieve operational status for the retrieval engine.

    Returns:
        dict[str, Any]: Dictionary representing the current retrieval status.

    """
    return retrieval_status(settings.qmd_command).__dict__


@log_skill_execution
def embedding_health() -> dict[str, Any]:
    """Return status for the local semantic embedding index.

    Returns:
        dict[str, Any]: Dictionary representing the local embedding status.

    """
    return embedding_status(
        settings.embedding_index_path,
        provider=settings.embedding_provider,
        model_name=settings.embedding_model_name,
        endpoint=settings.embedding_endpoint,
        dimensions=settings.embedding_dimensions,
    ).__dict__


@log_skill_execution
def index_zettelbrain_embeddings() -> dict[str, Any]:
    """Rebuild the local embedding index for Markdown files in the ZettelBrain.

    Returns:
        dict[str, Any]: Summary details of the generated embedding index.

    """
    index = build_embedding_index(
        settings.zettelkasten_path,
        settings.embedding_index_path,
        provider=settings.embedding_provider,
        dimensions=settings.embedding_dimensions,
        model_name=settings.embedding_model_name,
        endpoint=settings.embedding_endpoint,
    )
    return {
        "provider": index["provider"],
        "model_name": index["model_name"],
        "index_path": str(settings.embedding_index_path),
        "document_count": len(index["documents"]),
        "dimensions": index["dimensions"],
        "indexed_at": index["indexed_at"],
    }


@log_skill_execution
def semantic_search_zettelbrain(query: str, limit: int = 8) -> list[dict[str, Any]]:
    """Search the ZettelBrain through the local semantic embedding index.

    Args:
        query: The semantic search query terms.
        limit: The maximum number of search results. Defaults to 8.

    Returns:
        list[dict[str, Any]]: List of dictionary mappings representing matching search results.

    """
    return [
        result.__dict__
        for result in semantic_search(
            settings.zettelkasten_path,
            settings.embedding_index_path,
            query,
            limit=limit,
            provider=settings.embedding_provider,
            dimensions=settings.embedding_dimensions,
            model_name=settings.embedding_model_name,
            endpoint=settings.embedding_endpoint,
        )
    ]


@log_skill_execution
def suggest_zettelbrain_links(relative_path: str, limit: int = 5) -> list[dict[str, Any]]:
    """Suggest semantic links for a specific note, excluding existing links.

    Args:
        relative_path: The relative path of the target note.
        limit: The maximum number of search results. Defaults to 5.

    Returns:
        list[dict[str, Any]]: List of dictionary mappings representing unlinked similar notes.

    """
    return [
        result.__dict__
        for result in suggest_note_links(
            settings.zettelkasten_path,
            settings.embedding_index_path,
            relative_path,
            limit=limit,
            provider=settings.embedding_provider,
            dimensions=settings.embedding_dimensions,
            model_name=settings.embedding_model_name,
            endpoint=settings.embedding_endpoint,
        )
    ]


@log_skill_execution
def list_zettelbrain_markdown() -> list[str]:
    """List all markdown files inside the ZettelBrain folder.

    Returns:
        list[str]: Relative path strings of markdown files.

    """
    return list_markdown_files(settings.zettelkasten_path)


@log_skill_execution
def get_semantic_bridge(
    min_similarity: float = 0.05,
    max_similarity: float = 0.4,
) -> dict[str, Any]:
    """Find a pair of semantically distant notes in the ZettelBrain to act as a cognitive bridge.

    Args:
        min_similarity: Minimum cosine similarity threshold. Defaults to 0.05.
        max_similarity: Maximum cosine similarity threshold. Defaults to 0.4.

    Returns:
        dict[str, Any]: Details of the two bridge notes, similarity score, titles, or status.

    """
    return find_semantic_bridge(
        settings.embedding_index_path,
        min_similarity=min_similarity,
        max_similarity=max_similarity,
    )


@log_skill_execution
def read_zettelbrain_markdown(relative_path: str) -> str:
    """Read the full content of a markdown file in the ZettelBrain.

    Args:
        relative_path: Relative path of the markdown file to read.

    Returns:
        str: UTF-8 decoded text content of the markdown file.

    """
    return read_markdown_file(settings.zettelkasten_path, relative_path)


@log_skill_execution
def write_zettelbrain_markdown(relative_path: str, content: str) -> str:
    """Write the UTF-8 content to a markdown file in the ZettelBrain safely.

    Args:
        relative_path: Relative path of the markdown file to write.
        content: The text content to write.

    Returns:
        str: Relative path of the written file.

    """
    return write_markdown_file(settings.zettelkasten_path, relative_path, content)


@log_skill_execution
def lint_zettelbrain() -> dict[str, Any]:
    """Run the static audit and validation linter for ZettelBrain.

    Identifies dead links, orphan notes, minimal graph connections,
    source-specific literature filename issues, and emergent patterns from
    bolded terms. The deterministic lint pass also renames fixable literature
    files and updates wikilinks.

    Returns:
        dict[str, Any]: Linting result structure.

    """
    return run_lint_logic()


@log_skill_execution
def inspect_pdf_manifest(source_path: str) -> dict[str, Any]:
    """Search and inspect the PageIndex manifest for a given PDF path.

    Args:
        source_path: The relative source path of the PDF.

    Returns:
        dict[str, Any]: Manifest details if found, otherwise an empty representation.

    """
    manifest = find_pageindex_manifest(settings.vault_path / ".pageindex", source_path)
    return manifest or {"found": False, "source_path": source_path}


@log_skill_execution
def list_pdf_manifests() -> list[dict[str, Any]]:
    """List all PageIndex manifests cached in the vault.

    Returns:
        list[dict[str, Any]]: List of metadata dictionaries representing cached manifests.

    """
    return list_pageindex_manifests(settings.vault_path / ".pageindex")


@log_skill_execution
def read_pdf_cache(
    document_id: str,
    query: str | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    """Read the PageIndex cache for a document ID, with optional term search.

    Args:
        document_id: Hexadecimal SHA-256 fingerprint identifying the document.
        query: Optional search term(s) to query against the tree.
        limit: Max search results matching the query. Defaults to 5.

    Returns:
        dict[str, Any]: Dictionary representing the document's manifest, tree
            and search matches.

    """
    return read_pageindex_cache(
        settings.vault_path / ".pageindex",
        document_id,
        query=query,
        limit=limit,
    )


@log_skill_execution
def resolve_pdf(relative_path: str) -> dict[str, Any]:
    """Resolve a PDF's document ID and verify if its cache exists in PageIndex.

    Args:
        relative_path: The relative path of the target PDF file.

    Returns:
        dict[str, Any]: Map containing source path, document ID, cache status and manifest.

    """
    return resolve_pdf_cache(
        settings.vault_path,
        settings.raw_papers_path,
        settings.vault_path / ".pageindex",
        relative_path,
    )


@log_skill_execution
def read_pdf_page(document_id: str, page: int) -> dict[str, Any]:
    """Retrieve the text content of a single page from a cached PDF.

    Args:
        document_id: Hexadecimal SHA-256 fingerprint identifying the document.
        page: 1-indexed page number to extract.

    Returns:
        dict[str, Any]: Page search status, manifest, text content and node count.

    """
    return read_pageindex_page(settings.vault_path / ".pageindex", document_id, page)


@log_skill_execution
def persist_pdf_cache(relative_path: str, tree_json: str) -> dict[str, Any]:
    """Persist a PageIndex tree and its manifest metadata to the cache directory.

    Args:
        relative_path: The relative path of the PDF source file.
        tree_json: JSON string representing the parsed layout/content tree structure.

    Returns:
        dict[str, Any]: Details of the persisted paths, document ID and manifest.

    """
    return persist_pageindex_cache(
        settings.vault_path,
        settings.raw_papers_path,
        settings.vault_path / ".pageindex",
        relative_path,
        tree_json,
    )


@log_skill_execution
def index_pdf_cache(relative_path: str) -> dict[str, Any]:
    """Run the configured external PageIndex command and persist its cache output.

    Args:
        relative_path: Relative path to the PDF inside raw/papers.

    Returns:
        dict[str, Any]: Metadata detailing the persisted cache structure.

    """
    return index_pdf_with_command(
        settings.vault_path,
        settings.raw_papers_path,
        settings.vault_path / ".pageindex",
        relative_path,
        pageindex_command=settings.pageindex_command,
    )


@log_skill_execution
def compute_pdf_sha256(relative_path: str) -> dict[str, str]:
    """Compute the SHA-256 checksum for a PDF inside raw/papers.

    Args:
        relative_path: Relative path to the PDF inside raw/papers.

    Returns:
        dict[str, str]: A dictionary with the source path and hexadecimal SHA-256 hash.

    Raises:
        ValueError: If the file is not a PDF or lies outside raw/papers.

    """
    pdf_path = (settings.vault_path / relative_path).resolve()
    if settings.raw_papers_path.resolve() not in pdf_path.parents:
        raise ValueError("Only PDFs inside raw/papers can be hashed by this tool.")
    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError("The provided file is not a PDF.")
    return {"source_path": relative_path, "document_id": sha256_file(pdf_path)}


@log_skill_execution
def estimate_pdf_processing(relative_path: str) -> dict[str, Any]:
    """Estimate the cost, tokens, and time required to process a PDF.

    Args:
        relative_path: The relative path of the PDF inside raw/papers.

    Returns:
        dict[str, Any]: Cost, token, and duration estimation details.

    """
    return estimate_document_processing(
        settings.vault_path,
        settings.raw_papers_path,
        settings.vault_path / ".pageindex",
        relative_path,
    )


@log_skill_execution
def ingest_web_article(url: str, filename: str | None = None) -> dict[str, Any]:
    """Ingest a web article from a URL and save it to raw/articles/ as Markdown.

    Args:
        url: The absolute HTTP/HTTPS URL of the web article.
        filename: Optional custom filename to save the article under.

    Returns:
        dict[str, Any]: A dictionary representing the outcome of the ingestion,
            containing keys such as 'status', 'output_path', and 'error' if any.

    """
    try:
        saved_path = save_raw_article(
            url=url,
            raw_articles_path=settings.raw_articles_path,
            filename=filename,
        )
        if saved_path:
            return {
                "status": "success",
                "output_path": str(saved_path.relative_to(settings.vault_path)).replace("\\", "/"),
            }
        return {
            "status": "error",
            "error": "Failed to extract article content.",
        }
    except Exception as exc:
        return {
            "status": "error",
            "error": str(exc),
        }


def build_server() -> Any:
    """Build and configure the FastMCP server instance.

    Returns:
        Any: Configured FastMCP server instance.

    Raises:
        RuntimeError: If FastMCP library cannot be imported.

    """
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:  # pragma: no cover - depends on runtime dependency
        raise RuntimeError("Instale as dependencias com `uv sync` antes de iniciar o MCP.") from exc

    server = FastMCP("ZettelBrain")
    server.tool()(health)
    server.tool()(search_zettelbrain)
    server.tool()(retrieval_health)
    server.tool()(embedding_health)
    server.tool()(index_zettelbrain_embeddings)
    server.tool()(semantic_search_zettelbrain)
    server.tool()(suggest_zettelbrain_links)
    server.tool()(list_zettelbrain_markdown)
    server.tool()(get_semantic_bridge)
    server.tool()(read_zettelbrain_markdown)
    server.tool()(write_zettelbrain_markdown)
    server.tool()(lint_zettelbrain)
    server.tool()(inspect_pdf_manifest)
    server.tool()(list_pdf_manifests)
    server.tool()(read_pdf_cache)
    server.tool()(resolve_pdf)
    server.tool()(read_pdf_page)
    server.tool()(persist_pdf_cache)
    server.tool()(index_pdf_cache)
    server.tool()(compute_pdf_sha256)
    server.tool()(estimate_pdf_processing)
    server.tool()(ingest_web_article)
    return server


def main() -> None:
    """Bootstrap entry point for running the MCP server or dumping health JSON.

    Returns:
        None

    """
    if "--health-json" in sys.argv:
        print(json.dumps(health(), ensure_ascii=False))
        return
    build_server().run()


if __name__ == "__main__":
    main()
