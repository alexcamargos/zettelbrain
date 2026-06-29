"""Search utilities for finding relevant documents inside the Obsidian ZettelBrain.

Provides hybrid search functions merging deterministic lexical word-count matching
with semantic index querying using the external `qmd` tool.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from math import log
from pathlib import Path

from tools_command import split_command


@dataclass(frozen=True)
class SearchResult:
    """Represents a search hit containing file path, ranking score and excerpt text.

    Attributes:
        path: Relative forward-slash path to the matched markdown file.
        score: Relevance score integer (higher is more relevant).
        excerpt: Snippet of matching text around the keywords.
        engine: The search engine used (e.g., 'bm25' or 'qmd').

    """

    path: str
    score: float
    excerpt: str
    engine: str = "bm25"


@dataclass(frozen=True)
class RetrievalStatus:
    """Describe the availability of the qmd-backed retrieval path."""

    qmd_configured: bool
    qmd_available: bool
    qmd_command: str | None
    fallback_engine: str = "bm25"


def hybrid_search(
    root: Path,
    query: str,
    *,
    limit: int = 8,
    qmd_command: str | None = "qmd",
) -> list[SearchResult]:
    """Execute hybrid search using qmd when available, with a lexical fallback.

    Args:
        root: Base Path directory of the ZettelBrain vault.
        query: Space-separated search terms to query.
        limit: Max search hits to return. Defaults to 8.
        qmd_command: Path/name of the qmd executable. Defaults to "qmd".

    Returns:
        list[SearchResult]: Ranked list of SearchResult matches.

    """
    if qmd_command:
        qmd_results = qmd_search(root, query, limit=limit, qmd_command=qmd_command)
        if qmd_results:
            return qmd_results
    return lexical_search(root, query, limit=limit)


def merge_search_results(
    primary: list[SearchResult],
    secondary: list[SearchResult],
    *,
    limit: int,
) -> list[SearchResult]:
    """Merge two ranked result sets, de-duplicating by path.

    Scores are summed when both engines find the same document; unique secondary
    hits are kept with their original score. This gives the MCP server a local
    hybrid fallback without forcing qmd availability.

    Args:
        primary: Primary search result list.
        secondary: Secondary search result list.
        limit: Maximum results to return after merging.

    Returns:
        list[SearchResult]: Merged and sorted list of search results.

    """
    merged: dict[str, SearchResult] = {}
    for result in [*primary, *secondary]:
        existing = merged.get(result.path)
        if existing is None:
            merged[result.path] = result
            continue
        merged[result.path] = SearchResult(
            path=result.path,
            score=round(existing.score + result.score, 6),
            excerpt=existing.excerpt or result.excerpt,
            engine=_merge_engine_names(existing.engine, result.engine),
        )
    return sorted(merged.values(), key=lambda result: (-result.score, result.path))[:limit]


def retrieval_status(qmd_command: str | None = "qmd") -> RetrievalStatus:
    """Return availability information for the retrieval stack.

    Args:
        qmd_command: Optional executable command for qmd search tool. Defaults to "qmd".

    Returns:
        RetrievalStatus: Availability and configuration status of retrieval tools.

    """
    if not qmd_command:
        return RetrievalStatus(qmd_configured=False, qmd_available=False, qmd_command=None)
    command_args = split_command(qmd_command)
    executable = command_args[0]
    return RetrievalStatus(
        qmd_configured=True,
        qmd_available=shutil.which(executable) is not None,
        qmd_command=qmd_command,
    )


def lexical_search(root: Path, query: str, *, limit: int = 8) -> list[SearchResult]:
    """Scan files using local BM25 ranking.

    Args:
        root: Base Path directory of the ZettelBrain vault.
        query: Search query text.
        limit: Maximum results to return. Defaults to 8.

    Returns:
        list[SearchResult]: Ranked list of SearchResult matches.

    """
    terms = _tokenize(query)
    if not terms:
        return []

    documents: list[tuple[Path, str, list[str]]] = []
    for path in root.rglob("*.md"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        tokens = _tokenize(text)
        if tokens:
            documents.append((path, text, tokens))

    if not documents:
        return []

    document_count = len(documents)
    average_length = sum(len(tokens) for _, _, tokens in documents) / document_count
    document_frequency = {
        term: sum(1 for _, _, tokens in documents if term in set(tokens)) for term in set(terms)
    }

    results: list[SearchResult] = []
    for path, text, tokens in documents:
        score = _bm25_score(
            query_terms=terms,
            document_terms=tokens,
            document_frequency=document_frequency,
            document_count=document_count,
            average_length=average_length,
        )
        if score <= 0:
            continue
        results.append(
            SearchResult(
                path=str(path.relative_to(root)).replace("\\", "/"),
                score=score,
                excerpt=_excerpt(text, terms),
            )
        )
    return sorted(results, key=lambda result: (-result.score, result.path))[:limit]


def qmd_search(
    root: Path,
    query: str,
    *,
    limit: int = 8,
    qmd_command: str = "qmd",
) -> list[SearchResult]:
    """Invoke the external `qmd` CLI tool for semantic vector-based search.

    Args:
        root: Base Path directory of the ZettelBrain vault.
        query: Search query text.
        limit: Maximum results to return. Defaults to 8.
        qmd_command: Command prefix to execute qmd. Defaults to "qmd".

    Returns:
        list[SearchResult]: Ranked list of SearchResult matches or empty list on error.

    """
    command_args = split_command(qmd_command)
    executable = command_args[0]
    if shutil.which(executable) is None:
        return []

    command = [
        *command_args,
        "search",
        query,
        "--limit",
        str(limit),
    ]
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            cwd=root,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []

    if completed.returncode != 0:
        return []
    return _parse_qmd_output(completed.stdout, root=root, limit=limit)


def _excerpt(text: str, terms: list[str], *, radius: int = 180) -> str:
    """Extract snippet context around the first matched search term.

    Args:
        text: Target text to slice.
        terms: List of matching search terms.
        radius: Number of characters to capture before and after the term index.
            Defaults to 180.

    Returns:
        str: Cleaned text snippet containing the match context.

    """
    lowered = text.lower()
    positions = [lowered.find(term) for term in terms if lowered.find(term) >= 0]
    if not positions:
        return text[: radius * 2].strip()
    start = max(min(positions) - radius, 0)
    end = min(min(positions) + radius, len(text))
    return re.sub(r"\s+", " ", text[start:end]).strip()


def _parse_qmd_output(output: str, *, root: Path, limit: int) -> list[SearchResult]:
    """Parse standard stdout lines printed by qmd CLI search into SearchResults.

    Args:
        output: Raw stdout text from qmd executable process.
        root: ZettelBrain root directory Path.
        limit: Maximum results to parse.

    Returns:
        list[SearchResult]: List of parsed SearchResult objects.

    """
    results: list[SearchResult] = []
    for line_number, raw_line in enumerate(output.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        path_text, excerpt = _split_qmd_result_line(line)
        path = Path(path_text.strip())
        if path.is_absolute():
            try:
                relative_path = path.relative_to(root)
            except ValueError:
                relative_path = Path(path.name)
        else:
            relative_path = path
        results.append(
            SearchResult(
                path=str(relative_path).replace("\\", "/"),
                score=float(max(limit - line_number + 1, 1)),
                excerpt=excerpt.strip() or line,
                engine="qmd",
            )
        )
        if len(results) >= limit:
            break
    return results


def _split_qmd_result_line(line: str) -> tuple[str, str]:
    """Split a qmd result line into path and excerpt without breaking Windows drive letters.

    Args:
        line: A single stdout line emitted by qmd.

    Returns:
        tuple[str, str]: The extracted path text and excerpt text.

    """
    match = re.match(
        r"^(?P<path>(?:[A-Za-z]:)?[^:]+?\.md)\s*:\s*(?P<excerpt>.*)$",
        line,
    )
    if match:
        return match.group("path"), match.group("excerpt")

    path_text, _, excerpt = line.partition(":")
    return path_text, excerpt


def _tokenize(text: str) -> list[str]:
    """Tokenize and normalize text into word lists.

    Args:
        text: The text content to tokenize.

    Returns:
        list[str]: Lowercase word token list of at least 2 characters.

    """
    return [term.lower() for term in re.findall(r"\w+", text) if len(term) >= 2]


def _merge_engine_names(left: str, right: str) -> str:
    """Combine and deduplicate engine name tags.

    Args:
        left: Left operand engine name string.
        right: Right operand engine name string.

    Returns:
        str: Combined engine names joined by a plus sign.

    """
    names = []
    for name in [*left.split("+"), *right.split("+")]:
        if name not in names:
            names.append(name)
    return "+".join(names)


def _bm25_score(
    *,
    query_terms: list[str],
    document_terms: list[str],
    document_frequency: dict[str, int],
    document_count: int,
    average_length: float,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    """Calculate the BM25 relevance score for a document.

    Args:
        query_terms: Token list of the query.
        document_terms: Token list of the document content.
        document_frequency: Corpus frequencies of query terms.
        document_count: Total count of documents in corpus.
        average_length: Average length of documents in corpus.
        k1: Term frequency saturation tuning parameter. Defaults to 1.5.
        b: Document length normalization tuning parameter. Defaults to 0.75.

    Returns:
        float: BM25 score.

    """
    term_counts = {term: document_terms.count(term) for term in set(query_terms)}
    document_length = len(document_terms)
    score = 0.0

    for term in query_terms:
        frequency = term_counts.get(term, 0)
        if frequency <= 0:
            continue
        frequency_in_corpus = document_frequency.get(term, 0)
        inverse_document_frequency = log(
            1 + (document_count - frequency_in_corpus + 0.5) / (frequency_in_corpus + 0.5)
        )
        denominator = frequency + k1 * (1 - b + b * (document_length / max(average_length, 1.0)))
        score += inverse_document_frequency * ((frequency * (k1 + 1)) / denominator)

    return round(score, 6)
