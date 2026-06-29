"""Unit tests for the find_semantic_bridge utility and _extract_title helper."""

from __future__ import annotations

from pathlib import Path

import pytest
from tools_embeddings import build_embedding_index, find_semantic_bridge


def test_find_semantic_bridge_missing_index() -> None:
    """Test that find_semantic_bridge raises FileNotFoundError if index does not exist.

    Returns:
        None

    """
    with pytest.raises(FileNotFoundError):
        find_semantic_bridge(Path("invalid/index_path.json"))


def test_find_semantic_bridge_insufficient_documents(tmp_path: Path) -> None:
    """Test find_semantic_bridge behavior with fewer than 2 indexed documents.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        None

    """
    zettelbrain = tmp_path / "zettelbrain"
    permanent = zettelbrain / "permanent"
    permanent.mkdir(parents=True)
    (permanent / "note1.md").write_text("credito cooperativo risco", encoding="utf-8")
    index_path = tmp_path / ".state" / "embeddings_index.json"

    build_embedding_index(
        zettelbrain,
        index_path,
        provider="hashing",
        dimensions=32,
        model_name="nomic-embed-text",
        endpoint=None,
    )

    result = find_semantic_bridge(index_path)
    assert result["status"] == "error"
    assert "Not enough documents" in result["message"]


def test_find_semantic_bridge_success(tmp_path: Path) -> None:
    """Test find_semantic_bridge successfully finds a distant note pair.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        None

    """
    zettelbrain = tmp_path / "zettelbrain"
    permanent = zettelbrain / "permanent"
    permanent.mkdir(parents=True)

    # Create two files. To control similarity with deterministic hashing,
    # we use distinct vocabulary.
    (permanent / "note1.md").write_text(
        "# Crédito Cooperativo\nAnálise de risco de cooperativas.", encoding="utf-8"
    )
    (permanent / "note2.md").write_text(
        "# Redes GAN\nPrevisão sintética de imagens adversariais.", encoding="utf-8"
    )
    index_path = tmp_path / ".state" / "embeddings_index.json"

    build_embedding_index(
        zettelbrain,
        index_path,
        provider="hashing",
        dimensions=64,
        model_name="nomic-embed-text",
        endpoint=None,
    )

    result = find_semantic_bridge(index_path, min_similarity=-1.0, max_similarity=1.0)
    assert result["status"] == "success"
    assert "similarity" in result
    assert result["note_a"]["title"] == "Crédito Cooperativo"
    assert result["note_b"]["title"] == "Redes GAN"


def test_find_semantic_bridge_no_match(tmp_path: Path) -> None:
    """Test find_semantic_bridge returns no_bridge_found when similarity constraints are too tight.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        None

    """
    zettelbrain = tmp_path / "zettelbrain"
    permanent = zettelbrain / "permanent"
    permanent.mkdir(parents=True)
    (permanent / "note1.md").write_text("credito cooperativo", encoding="utf-8")
    (permanent / "note2.md").write_text("credito cooperativo", encoding="utf-8")
    index_path = tmp_path / ".state" / "embeddings_index.json"

    build_embedding_index(
        zettelbrain,
        index_path,
        provider="hashing",
        dimensions=32,
        model_name="nomic-embed-text",
        endpoint=None,
    )

    # Note 1 and Note 2 will be identical, so similarity is 1.0.
    # Range [0.0, 0.5] should yield no results.
    result = find_semantic_bridge(index_path, min_similarity=0.0, max_similarity=0.5)
    assert result["status"] == "no_bridge_found"
    assert "No notes were found" in result["message"]
