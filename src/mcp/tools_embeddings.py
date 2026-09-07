"""Local embedding index utilities for semantic retrieval.

The current implementation uses deterministic hashing embeddings as an offline
fallback. It keeps the MCP retrieval layer functional without requiring a local
model runtime; a model-backed provider can replace `hashing_embedding` later
without changing the persisted index contract.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import re
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from logger import get_logger

SCHEMA_VERSION = "1"
DEFAULT_PROVIDER = "hashing"
FALLBACK_PROVIDER = "hashing"
MIN_TOKEN_LENGTH = 2
DEFAULT_TIMEOUT_SECONDS = 20
INDEXABLE_EMBEDDING_DIRS = ("literature", "permanent")
HASHING_PORTUGUESE_STOP_WORDS = frozenset(
    {
        "a",
        "as",
        "ate",
        "com",
        "como",
        "contra",
        "da",
        "das",
        "de",
        "dele",
        "deles",
        "depois",
        "do",
        "dos",
        "e",
        "ela",
        "elas",
        "ele",
        "eles",
        "em",
        "entre",
        "era",
        "eram",
        "essa",
        "essas",
        "esse",
        "esses",
        "esta",
        "estao",
        "estar",
        "estas",
        "estava",
        "este",
        "estes",
        "eu",
        "ja",
        "mais",
        "mas",
        "me",
        "mesmo",
        "meu",
        "meus",
        "minha",
        "minhas",
        "muito",
        "na",
        "nao",
        "nas",
        "no",
        "nos",
        "nossa",
        "nossas",
        "nosso",
        "nossos",
        "o",
        "os",
        "ou",
        "para",
        "pela",
        "pelas",
        "pelo",
        "pelos",
        "por",
        "porque",
        "qual",
        "quando",
        "que",
        "quem",
        "sao",
        "se",
        "sem",
        "ser",
        "seu",
        "seus",
        "sua",
        "suas",
        "t\u00e3o",
        "tambem",
        "tamb\u00e9m",
        "te",
        "tem",
        "um",
        "uma",
        "umas",
        "uns",
        "voce",
        "voc\u00ea",
    }
)

HASHING_ENGLISH_STOP_WORDS = frozenset(
    {
        "a",
        "about",
        "above",
        "after",
        "again",
        "against",
        "ain",
        "all",
        "also",
        "am",
        "an",
        "and",
        "any",
        "are",
        "aren",
        "as",
        "at",
        "be",
        "because",
        "been",
        "before",
        "being",
        "below",
        "between",
        "both",
        "but",
        "by",
        "can",
        "does",
        "doing",
        "don",
        "down",
        "during",
        "each",
        "few",
        "for",
        "from",
        "further",
        "has",
        "have",
        "having",
        "he",
        "her",
        "here",
        "hers",
        "herself",
        "him",
        "himself",
        "his",
        "how",
        "i",
        "if",
        "in",
        "into",
        "is",
        "it",
        "its",
        "itself",
        "just",
        "more",
        "most",
        "my",
        "myself",
        "no",
        "nor",
        "not",
        "now",
        "of",
        "off",
        "on",
        "once",
        "only",
        "or",
        "our",
        "ours",
        "ourselves",
        "out",
        "over",
        "own",
        "she",
        "should",
        "so",
        "some",
        "such",
        "than",
        "that",
        "the",
        "their",
        "theirs",
        "them",
        "themselves",
        "then",
        "there",
        "these",
        "they",
        "this",
        "those",
        "through",
        "to",
        "too",
        "until",
        "up",
        "very",
        "was",
        "we",
        "were",
        "what",
        "when",
        "where",
        "which",
        "while",
        "who",
        "whom",
        "why",
        "will",
        "with",
        "you",
        "your",
        "yours",
        "yourself",
        "yourselves",
    }
)
HASHING_STOP_WORDS = HASHING_PORTUGUESE_STOP_WORDS | HASHING_ENGLISH_STOP_WORDS


@dataclass(frozen=True)
class EmbeddingSearchResult:
    """Represents a semantic search result from the local embedding index.

    Attributes:
        path: Relative forward-slash path to the matched markdown file.
        score: Cosine similarity score.
        excerpt: Snippet of matching text around the keywords.
        engine: Name of the embedding engine used.

    """

    path: str
    score: float
    excerpt: str
    engine: str = "hash-embedding"


@dataclass(frozen=True)
class EmbeddingStatus:
    """Operational status for the local embedding index.

    Attributes:
        provider: The configured embedding provider name.
        active_provider: The active embedding provider name.
        model_name: Name of the embedding model.
        endpoint: Endpoint URL for API-based embedding providers.
        index_path: Absolute path to the index JSON file.
        index_exists: True if the index file exists.
        document_count: Number of documents indexed.
        dimensions: Vector space dimensionality of the embeddings.
        fallback_provider: Optional fallback embedding provider name.

    """

    provider: str
    active_provider: str
    model_name: str
    endpoint: str | None
    index_path: str
    index_exists: bool
    document_count: int
    dimensions: int
    fallback_provider: str | None


def embedding_status(
    index_path: Path,
    *,
    provider: str,
    model_name: str,
    endpoint: str | None,
    dimensions: int,
) -> EmbeddingStatus:
    """Return availability and size information for the local embedding index.

    Args:
        index_path: Absolute path to the local embedding index JSON file.
        provider: Configured embedding provider name.
        model_name: Name of the default embedding model.
        endpoint: Local embedding endpoint URL.
        dimensions: Number of dimensions in the local embedding vector.

    Returns:
        EmbeddingStatus: Operational status values mapping.

    """
    index = _load_index(index_path)
    index_provider = str(index.get("provider", provider)) if index else provider
    fallback_provider = index.get("fallback_provider") if index else None
    return EmbeddingStatus(
        provider=provider,
        active_provider=index_provider,
        model_name=model_name,
        endpoint=endpoint,
        index_path=str(index_path),
        index_exists=index_path.exists(),
        document_count=len(index.get("documents", [])) if index else 0,
        dimensions=int(index.get("dimensions", dimensions)) if index else dimensions,
        fallback_provider=str(fallback_provider) if fallback_provider else None,
    )


def build_embedding_index(
    root: Path,
    index_path: Path,
    *,
    provider: str,
    dimensions: int,
    model_name: str,
    endpoint: str | None,
) -> dict[str, Any]:
    """Build and persist a local embedding index for Markdown files under root.

    Args:
        root: Root folder Path to scan for files.
        index_path: Absolute path to save the index JSON.
        provider: Configured embedding provider name (e.g. 'hashing' or 'ollama').
        dimensions: Target dimensions size.
        model_name: Name of the default embedding model.
        endpoint: Endpoint URL for API-based providers.

    Returns:
        dict[str, Any]: Payload dictionary stored in the index path.

    """
    embedder = _resolve_embedder(
        provider=provider,
        model_name=model_name,
        endpoint=endpoint,
        dimensions=dimensions,
    )
    documents: list[dict[str, Any]] = []
    for path in _iter_indexable_markdown(root):
        text = path.read_text(encoding="utf-8", errors="ignore")
        embedding = embedder.embed(text)
        if not any(embedding):
            continue
        documents.append(
            {
                "path": str(path.relative_to(root)).replace("\\", "/"),
                "embedding": embedding,
                "text_length": len(text),
            }
        )

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "provider": embedder.active_provider,
        "configured_provider": provider,
        "fallback_provider": embedder.fallback_provider,
        "model_name": model_name,
        "dimensions": len(documents[0]["embedding"]) if documents else dimensions,
        "endpoint": endpoint if provider == "ollama" else None,
        "indexed_at": datetime.now(UTC).isoformat(),
        "root": str(root),
        "documents": documents,
    }
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return payload


def _iter_indexable_markdown(root: Path) -> Iterator[Path]:
    """Yield Markdown files from conceptual note folders only.

    Args:
        root: Root folder Path to scan for files.

    Yields:
        Path: Markdown file Paths inside active conceptual directories.

    """
    for directory_name in INDEXABLE_EMBEDDING_DIRS:
        directory = root / directory_name
        if not directory.is_dir():
            continue
        yield from sorted(directory.rglob("*.md"))


def semantic_search(
    root: Path,
    index_path: Path,
    query: str,
    *,
    limit: int,
    provider: str,
    dimensions: int,
    model_name: str,
    endpoint: str | None,
    rebuild_if_missing: bool = True,
) -> list[EmbeddingSearchResult]:
    """Search the local embedding index using cosine similarity.

    Args:
        root: Root folder Path containing the ZettelBrain files.
        index_path: Absolute path to the index JSON.
        query: Semantic search query terms.
        limit: Maximum results to return.
        provider: Configured embedding provider name.
        dimensions: Target dimensions size.
        model_name: Name of the default embedding model.
        endpoint: Endpoint URL for API-based providers.
        rebuild_if_missing: Automatically build index if file does not exist.

    Returns:
        list[EmbeddingSearchResult]: Sorted list of search results.

    """
    index = _load_index(index_path)
    if index is None and rebuild_if_missing:
        index = build_embedding_index(
            root,
            index_path,
            provider=provider,
            dimensions=dimensions,
            model_name=model_name,
            endpoint=endpoint,
        )
    if not index:
        return []

    index_dimensions = int(index.get("dimensions", dimensions))
    active_provider = str(index.get("provider", provider))

    if provider != active_provider:
        raise ValueError(
            "Incompatibilidade de embeddings detectada: O índice local foi construído utilizando "
            f"o provedor '{active_provider}', mas a configuração/busca atual solicita "
            f"'{provider}'. "
            f"Se você deseja usar '{provider}', certifique-se de que o provedor está online e "
            "execute a ferramenta 'index_zettelbrain_embeddings' para reconstruir o índice. Caso "
            "contrário, altere a configuração do EMBEDDING_PROVIDER para coincidir com o índice."
        )
    query_embedding = embed_text(
        query,
        provider=active_provider,
        model_name=model_name,
        endpoint=endpoint,
        dimensions=index_dimensions,
    )
    if not any(query_embedding):
        return []

    results: list[EmbeddingSearchResult] = []
    for document in index.get("documents", []):
        path_text = document.get("path")
        embedding = document.get("embedding")
        if not isinstance(path_text, str) or not isinstance(embedding, list):
            continue
        score = cosine_similarity(query_embedding, embedding)
        if score <= 0:
            continue
        markdown_path = (root / path_text).resolve()
        excerpt = ""
        if markdown_path.exists() and root.resolve() in markdown_path.parents:
            excerpt = _excerpt(markdown_path.read_text(encoding="utf-8", errors="ignore"), query)
        results.append(
            EmbeddingSearchResult(
                path=path_text.replace("\\", "/"),
                score=round(score, 6),
                excerpt=excerpt,
                engine=_engine_name(active_provider),
            )
        )

    return sorted(results, key=lambda result: (-result.score, result.path))[:limit]


def suggest_note_links(
    root: Path,
    index_path: Path,
    relative_path: str,
    *,
    limit: int,
    provider: str,
    dimensions: int,
    model_name: str,
    endpoint: str | None,
    rebuild_if_missing: bool = True,
) -> list[EmbeddingSearchResult]:
    """Suggest semantic links for a specific note, excluding existing links.

    Args:
        root: Root folder Path containing the ZettelBrain files.
        index_path: Absolute path to the index JSON.
        relative_path: Relative path of the target note.
        limit: Maximum results to return.
        provider: Configured embedding provider name.
        dimensions: Target dimensions size.
        model_name: Name of the default embedding model.
        endpoint: Endpoint URL for API-based providers.
        rebuild_if_missing: Automatically build index if file does not exist.

    Returns:
        list[EmbeddingSearchResult]: Sorted list of search results not currently linked.

    Raises:
        FileNotFoundError: If the target file does not exist.
        ValueError: If there's an embedding provider mismatch.

    """
    target_path = (root / relative_path).resolve()
    if not target_path.exists() or not target_path.is_file():
        raise FileNotFoundError(f"File not found: {relative_path}")

    content = target_path.read_text(encoding="utf-8", errors="ignore")

    excluded_slugs = {target_path.stem.lower()}
    for match in re.findall(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]", content):
        excluded_slugs.add(match.strip().lower())

    index = _load_index(index_path)
    if index is None and rebuild_if_missing:
        index = build_embedding_index(
            root,
            index_path,
            provider=provider,
            dimensions=dimensions,
            model_name=model_name,
            endpoint=endpoint,
        )
    if not index:
        return []

    index_dimensions = int(index.get("dimensions", dimensions))
    active_provider = str(index.get("provider", provider))

    if provider != active_provider:
        raise ValueError(
            "Incompatibilidade de embeddings detectada: O índice local foi construído utilizando "
            f"o provedor '{active_provider}', mas a configuração/busca atual solicita "
            f"'{provider}'. "
            f"Se você deseja usar '{provider}', certifique-se de que o provedor está online e "
            "execute a ferramenta 'index_zettelbrain_embeddings' para reconstruir o índice. Caso "
            "contrário, altere a configuração do EMBEDDING_PROVIDER para coincidir com o índice."
        )

    query_embedding = embed_text(
        content,
        provider=active_provider,
        model_name=model_name,
        endpoint=endpoint,
        dimensions=index_dimensions,
    )

    if not any(query_embedding):
        return []

    results: list[EmbeddingSearchResult] = []
    for document in index.get("documents", []):
        path_text = document.get("path")
        embedding = document.get("embedding")
        if not isinstance(path_text, str) or not isinstance(embedding, list):
            continue

        doc_slug = Path(path_text).stem.lower()
        if doc_slug in excluded_slugs:
            continue

        score = cosine_similarity(query_embedding, embedding)
        if score <= 0:
            continue

        excerpt = ""
        markdown_path = (root / path_text).resolve()
        if markdown_path.exists() and root.resolve() in markdown_path.parents:
            doc_content = markdown_path.read_text(encoding="utf-8", errors="ignore")
            clean_text = re.sub(r"---.*?---", "", doc_content, flags=re.DOTALL).strip()
            excerpt = re.sub(r"\s+", " ", clean_text[:180]).strip()

        results.append(
            EmbeddingSearchResult(
                path=path_text.replace("\\", "/"),
                score=round(score, 6),
                excerpt=excerpt,
                engine=_engine_name(active_provider),
            )
        )

    return sorted(results, key=lambda result: (-result.score, result.path))[:limit]


def hashing_embedding(text: str, *, dimensions: int) -> list[float]:
    """Generate a normalized signed hashing vector for text.

    Args:
        text: Input text content to embed.
        dimensions: Dimensionality size of the target vector space.

    Returns:
        list[float]: Normalized vector representing the deterministic sign-hashes.

    Raises:
        ValueError: If dimensions is less than or equal to zero.

    """
    if dimensions <= 0:
        raise ValueError("dimensions deve ser maior que zero.")

    vector = [0.0] * dimensions
    for token in _tokenize_embedding_text(text):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [round(value / norm, 8) for value in vector]


def ollama_embedding(
    text: str,
    *,
    endpoint: str,
    model_name: str,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> list[float]:
    """Request an embedding vector from a local Ollama-compatible endpoint.

    Args:
        text: Input text content to embed.
        endpoint: Target Ollama server api endpoint URL.
        model_name: Model identifier name.
        timeout_seconds: Network connection timeout threshold.

    Returns:
        list[float]: Retrieved embedding vector values.

    Raises:
        RuntimeError: If the remote endpoint request fails.

    """
    payload = json.dumps({"model": model_name, "prompt": text}).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw_body = response.read().decode("utf-8")
    except (OSError, urllib.error.URLError) as exc:
        raise RuntimeError("Could not query the local embeddings endpoint.") from exc

    body = json.loads(raw_body)
    embedding = body.get("embedding")
    if not isinstance(embedding, list) or not embedding:
        raise RuntimeError("Embedding response did not include a valid vector.")
    return [float(value) for value in embedding]


def embed_text(
    text: str,
    *,
    provider: str,
    model_name: str,
    endpoint: str | None,
    dimensions: int,
) -> list[float]:
    """Embed text using the configured provider.

    Args:
        text: Input text content to embed.
        provider: Configured embedding provider name (e.g. 'hashing' or 'ollama').
        model_name: Model identifier name.
        endpoint: Endpoint URL for API-based providers.
        dimensions: Target dimensions size.

    Returns:
        list[float]: Normalized vector representing the text embedding.

    Raises:
        RuntimeError: If provider is ollama and endpoint is missing.

    """
    if provider == "ollama":
        if not endpoint:
            raise RuntimeError("EMBEDDING_ENDPOINT is not configured for the ollama provider.")
        return _normalize(ollama_embedding(text, endpoint=endpoint, model_name=model_name))
    return hashing_embedding(text, dimensions=dimensions)


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Compute cosine similarity between two normalized vectors.

    Args:
        left: Left operand vector.
        right: Right operand vector.

    Returns:
        float: Dot product of both normalized vectors.

    """
    if len(left) != len(right):
        return 0.0
    return sum(a * b for a, b in zip(left, right, strict=True))


class Embedder(ABC):
    """Abstract base class representing a text embedding generator.

    Attributes:
        active_provider: The active embedding provider string.
        fallback_provider: Optional fallback embedding provider string.
        model_name: Name of the embedding model.
        endpoint: Endpoint URL for API-based embedding providers.
        dimensions: Vector space dimensionality of the embeddings.

    """

    def __init__(
        self,
        *,
        active_provider: str,
        fallback_provider: str | None = None,
        model_name: str,
        endpoint: str | None = None,
        dimensions: int,
    ) -> None:
        """Initialize the base Embedder settings.

        Args:
            active_provider: The active embedding provider string.
            fallback_provider: Optional fallback embedding provider string.
            model_name: Name of the embedding model.
            endpoint: Endpoint URL for API-based embedding providers.
            dimensions: Vector space dimensionality of the embeddings.

        """
        self.active_provider = active_provider
        self.fallback_provider = fallback_provider
        self.model_name = model_name
        self.endpoint = endpoint
        self.dimensions = dimensions

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Generate a normalized embedding vector for the input text.

        Args:
            text: The input text to embed.

        Returns:
            list[float]: The generated and normalized embedding vector.

        Raises:
            RuntimeError: If vector generation fails.

        """
        pass


class HashingEmbedder(Embedder):
    """Deterministic signed hashing text embedding generator."""

    def __init__(
        self,
        *,
        model_name: str,
        endpoint: str | None = None,
        dimensions: int,
    ) -> None:
        """Initialize HashingEmbedder.

        Args:
            model_name: Name of the embedding model.
            endpoint: Endpoint URL for API-based embedding providers (ignored).
            dimensions: Vector space dimensionality of the embeddings.

        """
        super().__init__(
            active_provider="hashing",
            fallback_provider=None,
            model_name=model_name,
            endpoint=endpoint,
            dimensions=dimensions,
        )

    def embed(self, text: str) -> list[float]:
        """Generate a deterministic signed hashing vector for text.

        Args:
            text: The input text to embed.

        Returns:
            list[float]: The generated and normalized embedding vector.

        """
        return hashing_embedding(text, dimensions=self.dimensions)


class OllamaEmbedder(Embedder):
    """Local Ollama-compatible HTTP endpoint embedding generator."""

    def __init__(
        self,
        *,
        model_name: str,
        endpoint: str,
        dimensions: int,
        fallback_provider: str | None = None,
    ) -> None:
        """Initialize OllamaEmbedder.

        Args:
            model_name: Name of the embedding model.
            endpoint: Endpoint URL for Ollama service.
            dimensions: Vector space dimensionality of the embeddings.
            fallback_provider: Optional fallback embedding provider string.

        """
        super().__init__(
            active_provider="ollama",
            fallback_provider=fallback_provider,
            model_name=model_name,
            endpoint=endpoint,
            dimensions=dimensions,
        )

    def embed(self, text: str) -> list[float]:
        """Request an embedding vector from the local Ollama endpoint.

        Args:
            text: The input text to embed.

        Returns:
            list[float]: The generated and normalized embedding vector.

        Raises:
            RuntimeError: If request or vector generation fails.

        """
        return _normalize(
            ollama_embedding(
                text,
                endpoint=self.endpoint or "",
                model_name=self.model_name,
            )
        )


class EmbedderFactory:
    """Factory to instantiate and configure Embedder implementations."""

    @staticmethod
    def get_embedder(
        *,
        provider: str,
        model_name: str,
        endpoint: str | None,
        dimensions: int,
    ) -> Embedder:
        """Resolve and return the appropriate Embedder implementation.

        Checks provider type and validates availability, falling back to HashingEmbedder
        if the configured remote provider is unreachable.

        Args:
            provider: Configured embedding provider name (e.g. 'hashing' or 'ollama').
            model_name: Name of the embedding model.
            endpoint: Endpoint URL for API-based embedding providers.
            dimensions: Vector space dimensionality of the embeddings.

        Returns:
            Embedder: An initialized Embedder instance.

        """
        if provider != "ollama":
            return HashingEmbedder(
                model_name=model_name,
                endpoint=endpoint,
                dimensions=dimensions,
            )

        if not endpoint:
            return HashingEmbedder(
                model_name=model_name,
                endpoint=endpoint,
                dimensions=dimensions,
            )

        try:
            ollama_embedding(
                "healthcheck",
                endpoint=endpoint,
                model_name=model_name,
            )
        except RuntimeError:
            get_logger().warning(
                "Falha ao conectar ao Ollama. Usando fallback 'hashing' para os embeddings. "
                "Espaços vetoriais gerados serão incompatíveis com embeddings semânticos."
            )
            embedder = HashingEmbedder(
                model_name=model_name,
                endpoint=endpoint,
                dimensions=dimensions,
            )
            object.__setattr__(embedder, "fallback_provider", "hashing")
            return embedder

        return OllamaEmbedder(
            model_name=model_name,
            endpoint=endpoint,
            dimensions=dimensions,
        )


def _resolve_embedder(
    *,
    provider: str,
    model_name: str,
    endpoint: str | None,
    dimensions: int,
) -> Embedder:
    """Resolve and return an Embedder implementation using the EmbedderFactory.

    Args:
        provider: Configured embedding provider name.
        model_name: Name of the embedding model.
        endpoint: Endpoint URL for API-based embedding providers.
        dimensions: Vector space dimensionality of the embeddings.

    Returns:
        Embedder: An initialized Embedder instance.

    """
    return EmbedderFactory.get_embedder(
        provider=provider,
        model_name=model_name,
        endpoint=endpoint,
        dimensions=dimensions,
    )


def _normalize(vector: list[float]) -> list[float]:
    """Normalize vector magnitude using L2 norm.

    Args:
        vector: A list of floats to normalize.

    Returns:
        list[float]: The L2 normalized vector.

    """
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [round(value / norm, 8) for value in vector]


def _engine_name(provider: str) -> str:
    """Resolve retrieval engine label tag based on provider name.

    Args:
        provider: The provider name string.

    Returns:
        str: Standard engine tag name.

    """
    if provider == "ollama":
        return "ollama-embedding"
    return "hash-embedding"


def _load_index(index_path: Path) -> dict[str, Any] | None:
    """Read local JSON file index.

    Args:
        index_path: The index file Path.

    Returns:
        dict[str, Any] | None: Decoded index map if file exists and is valid JSON,
            otherwise None.

    """
    if not index_path.exists():
        return None
    try:
        payload = json.loads(index_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _excerpt(text: str, query: str, *, radius: int = 180) -> str:
    """Slices a contextual snippet around first query match within text.

    Args:
        text: Source text to extract context.
        query: Space-separated keyword string.
        radius: Number of characters to scan left and right. Defaults to 180.

    Returns:
        str: Excerpt snippet text.

    """
    terms = _tokenize(query)
    lowered = text.lower()
    positions = [lowered.find(term) for term in terms if lowered.find(term) >= 0]
    if not positions:
        return re.sub(r"\s+", " ", text[: radius * 2]).strip()
    start = max(min(positions) - radius, 0)
    end = min(min(positions) + radius, len(text))
    return re.sub(r"\s+", " ", text[start:end]).strip()


def _tokenize(text: str) -> list[str]:
    """Tokenize and normalize text into words of minimum length.

    Args:
        text: The source text to tokenize.

    Returns:
        list[str]: Normalized token word list.

    """
    return [token.lower() for token in re.findall(r"\w+", text) if len(token) >= MIN_TOKEN_LENGTH]


def _tokenize_embedding_text(text: str) -> list[str]:
    """Tokenize text for hashing embeddings, excluding common connector words.

    Args:
        text: The source text to tokenize for local hashing embeddings.

    Returns:
        list[str]: Tokens that should contribute to the deterministic hash vector.

    """
    return [token for token in _tokenize(text) if token not in HASHING_STOP_WORDS]


def _extract_title(path: Path) -> str:
    """Extract title from a Markdown file by checking its H1 header or path name.

    Args:
        path: Path to the markdown file.

    Returns:
        str: Extracted title.

    """
    if not path.exists():
        return path.name
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        yaml_match = re.search(r"title:\s*\"?([^\n\"]+)\"?", content)
        if yaml_match:
            return yaml_match.group(1).strip()
    except Exception:
        pass
    return path.stem


def find_semantic_bridge(
    index_path: Path,
    *,
    min_similarity: float = 0.05,
    max_similarity: float = 0.4,
) -> dict[str, Any]:
    """Find a pair of semantically distant documents in the index to act as a cognitive bridge.

    Args:
        index_path: The absolute path to the local embedding index JSON file.
        min_similarity: Minimum cosine similarity threshold (to avoid completely unrelated docs).
            Defaults to 0.05.
        max_similarity: Maximum cosine similarity threshold (to ensure they are
            semantically distant). Defaults to 0.4.

    Returns:
        dict[str, Any]: A dictionary containing details of the two bridge notes,
            their similarity score, and excerpts, or an error/status message
            if no bridge could be found.

    Raises:
        FileNotFoundError: If the index file does not exist.

    """
    index = _load_index(index_path)
    if index is None:
        raise FileNotFoundError(f"Index file not found at: {index_path}")

    documents = index.get("documents", [])
    if len(documents) < 2:
        return {
            "status": "error",
            "message": "Not enough documents in the index to establish a semantic bridge.",
        }

    root = Path(index.get("root", ""))

    pairs = []
    for i in range(len(documents)):
        for j in range(i + 1, len(documents)):
            similarity = cosine_similarity(documents[i]["embedding"], documents[j]["embedding"])
            if min_similarity <= similarity <= max_similarity:
                pairs.append((documents[i], documents[j], similarity))

    if not pairs:
        return {
            "status": "no_bridge_found",
            "message": (
                f"No notes were found in the similarity range [{min_similarity}, {max_similarity}]."
            ),
        }

    doc_a, doc_b, similarity = random.choice(pairs)
    path_a = root / doc_a["path"]
    path_b = root / doc_b["path"]

    return {
        "status": "success",
        "similarity": round(similarity, 6),
        "note_a": {
            "path": doc_a["path"],
            "title": _extract_title(path_a),
        },
        "note_b": {
            "path": doc_b["path"],
            "title": _extract_title(path_b),
        },
    }
