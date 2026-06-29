"""Unit tests for the local embedding index utilities."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from tools_embeddings import (
    build_embedding_index,
    embed_text,
    embedding_status,
    hashing_embedding,
    semantic_search,
)


def _write_note(root: Path, relative_path: str, content: str) -> None:
    """Write a Markdown note under a temporary ZettelBrain root."""
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_hashing_embedding_is_deterministic_and_normalized() -> None:
    """Test that hashing embeddings are stable and normalized for non-empty text.

    Returns:
        None

    """
    first = hashing_embedding("credito cooperativo risco", dimensions=32)
    second = hashing_embedding("credito cooperativo risco", dimensions=32)

    assert first == second
    assert len(first) == 32
    assert round(sum(value * value for value in first), 6) == 1.0


def test_hashing_embedding_ignores_common_stop_words() -> None:
    """Test that common Portuguese and English stop words do not affect hashing vectors.

    Returns:
        None

    """
    with_stop_words = hashing_embedding(
        "credito para com uma cooperativo and the with",
        dimensions=32,
    )
    without_stop_words = hashing_embedding("credito cooperativo", dimensions=32)

    assert with_stop_words == without_stop_words


def test_hashing_embedding_returns_zero_vector_for_only_stop_words() -> None:
    """Test that text containing only stop words produces an empty hashing vector.

    Returns:
        None

    """
    vector = hashing_embedding("para com uma este and the with for", dimensions=16)

    assert vector == [0.0] * 16


def test_build_embedding_index_and_semantic_search_rank_relevant_doc(tmp_path: Path) -> None:
    """Test persisted embedding index creation and semantic ranking.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        None

    """
    zettelbrain = tmp_path / "zettelbrain"
    zettelbrain.mkdir()
    _write_note(
        zettelbrain,
        "permanent/credito.md",
        "credito cooperativo risco insolvencia capital",
    )
    _write_note(
        zettelbrain,
        "literature/gan.md",
        "redes generativas adversariais imagem sintetica",
    )
    index_path = tmp_path / ".state" / "embeddings_index.json"

    index = build_embedding_index(
        zettelbrain,
        index_path,
        provider="hashing",
        dimensions=64,
        model_name="nomic-embed-text",
        endpoint=None,
    )
    results = semantic_search(
        zettelbrain,
        index_path,
        "risco de credito",
        limit=2,
        provider="hashing",
        dimensions=64,
        model_name="nomic-embed-text",
        endpoint=None,
    )

    assert index_path.exists()
    assert len(index["documents"]) == 2
    assert index["provider"] == "hashing"
    assert results[0].path == "permanent/credito.md"
    assert results[0].engine == "hash-embedding"


def test_build_embedding_index_only_includes_conceptual_note_folders(tmp_path: Path) -> None:
    """Test semantic indexing excludes drafts and root navigation Markdown files.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        None

    """
    zettelbrain = tmp_path / "zettelbrain"
    zettelbrain.mkdir()
    _write_note(zettelbrain, "literature/source.md", "fonte fichamento conceito")
    _write_note(zettelbrain, "permanent/atomic.md", "nota atomica permanente")
    _write_note(zettelbrain, "drafts/temp.md", "rascunho incompleto temporario")
    _write_note(zettelbrain, "overview.md", "sumario vivo circular")
    _write_note(zettelbrain, "index.md", "pagina raiz navegacao")
    index_path = tmp_path / ".state" / "embeddings_index.json"

    index = build_embedding_index(
        zettelbrain,
        index_path,
        provider="hashing",
        dimensions=16,
        model_name="nomic-embed-text",
        endpoint=None,
    )

    indexed_paths = {document["path"] for document in index["documents"]}
    assert indexed_paths == {
        "literature/source.md",
        "permanent/atomic.md",
    }


def test_embedding_status_reports_existing_index(tmp_path: Path) -> None:
    """Test embedding_status counts indexed documents when cache exists.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        None

    """
    zettelbrain = tmp_path / "zettelbrain"
    zettelbrain.mkdir()
    _write_note(zettelbrain, "permanent/note.md", "indicador pearls")
    index_path = tmp_path / ".state" / "embeddings_index.json"
    build_embedding_index(
        zettelbrain,
        index_path,
        provider="hashing",
        dimensions=16,
        model_name="nomic-embed-text",
        endpoint=None,
    )

    status = embedding_status(
        index_path,
        provider="hashing",
        model_name="nomic-embed-text",
        endpoint=None,
        dimensions=16,
    )

    assert status.index_exists is True
    assert status.document_count == 1
    assert status.provider == "hashing"
    assert status.active_provider == "hashing"


def test_ollama_provider_falls_back_to_hashing_when_endpoint_fails(tmp_path: Path) -> None:
    """Test offline fallback if a configured Ollama endpoint is unavailable.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        None

    """
    zettelbrain = tmp_path / "zettelbrain"
    zettelbrain.mkdir()
    _write_note(zettelbrain, "permanent/note.md", "credito cooperativo")
    index_path = tmp_path / ".state" / "embeddings_index.json"

    index = build_embedding_index(
        zettelbrain,
        index_path,
        provider="ollama",
        dimensions=16,
        model_name="nomic-embed-text",
        endpoint="http://127.0.0.1:1/api/embeddings",
    )

    assert index["configured_provider"] == "ollama"
    assert index["provider"] == "hashing"
    assert index["fallback_provider"] == "hashing"


def test_embed_text_uses_hashing_provider() -> None:
    """Test public embed_text dispatch for the hashing provider.

    Returns:
        None

    """
    vector = embed_text(
        "pearls capital",
        provider="hashing",
        model_name="nomic-embed-text",
        endpoint=None,
        dimensions=24,
    )

    assert len(vector) == 24
    assert any(vector)


def test_embed_text_uses_ollama_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test public embed_text dispatch for a successful Ollama-compatible endpoint.

    Args:
        monkeypatch: Pytest monkeypatch utility fixture.

    Returns:
        None

    """

    class FakeResponse:
        def __enter__(self) -> FakeResponse:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self) -> bytes:
            return b'{"embedding": [3, 4]}'

    captured = SimpleNamespace(request=None)

    def fake_urlopen(request: object, timeout: int) -> FakeResponse:
        captured.request = request
        assert timeout == 20
        return FakeResponse()

    monkeypatch.setattr("tools_embeddings.urllib.request.urlopen", fake_urlopen)

    vector = embed_text(
        "texto",
        provider="ollama",
        model_name="nomic-embed-text",
        endpoint="http://localhost:11434/api/embeddings",
        dimensions=24,
    )

    assert captured.request is not None
    assert vector == [0.6, 0.8]


def test_semantic_search_labels_ollama_index_engine(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test semantic search labels results with the active index provider.

    Args:
        tmp_path: Pytest temporary directory fixture.
        monkeypatch: Pytest monkeypatch utility fixture.

    Returns:
        None

    """
    zettelbrain = tmp_path / "zettelbrain"
    zettelbrain.mkdir()
    _write_note(zettelbrain, "permanent/note.md", "credito cooperativo")
    index_path = tmp_path / ".state" / "embeddings_index.json"

    monkeypatch.setattr(
        "tools_embeddings.ollama_embedding",
        lambda text, **_kwargs: [1.0, 0.0] if "credito" in text else [0.0, 1.0],
    )

    build_embedding_index(
        zettelbrain,
        index_path,
        provider="ollama",
        dimensions=2,
        model_name="nomic-embed-text",
        endpoint="http://localhost:11434/api/embeddings",
    )
    results = semantic_search(
        zettelbrain,
        index_path,
        "credito",
        limit=1,
        provider="ollama",
        dimensions=2,
        model_name="nomic-embed-text",
        endpoint="http://localhost:11434/api/embeddings",
    )
    assert results[0].engine == "ollama-embedding"


def test_semantic_search_raises_value_error_on_provider_mismatch(
    tmp_path: Path,
) -> None:
    """Test semantic_search raises ValueError for provider mismatches.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        None

    """
    zettelbrain = tmp_path / "zettelbrain"
    zettelbrain.mkdir()
    _write_note(zettelbrain, "permanent/note.md", "credito")
    index_path = tmp_path / ".state" / "embeddings_index.json"

    build_embedding_index(
        zettelbrain,
        index_path,
        provider="hashing",
        dimensions=16,
        model_name="nomic-embed-text",
        endpoint=None,
    )

    with pytest.raises(ValueError, match="Incompatibilidade de embeddings detectada"):
        semantic_search(
            zettelbrain,
            index_path,
            "credito",
            limit=1,
            provider="ollama",
            dimensions=16,
            model_name="nomic-embed-text",
            endpoint="http://localhost:11434/api/embeddings",
            rebuild_if_missing=False,
        )
