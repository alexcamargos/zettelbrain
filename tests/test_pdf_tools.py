"""Unit tests for the PageIndex layout cache and PDF indexing utilities.

Tests SHA-256 fingerprinting, cache resolution, manifest loading, and cache persistence.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from tools_pdf import (
    estimate_document_processing,
    index_pdf_with_command,
    list_pageindex_manifests,
    persist_pageindex_cache,
    read_pageindex_cache,
    read_pageindex_page,
    resolve_pdf_cache,
    sha256_file,
)


def test_sha256_file(tmp_path: Path) -> None:
    """Test that sha256_file computes the correct SHA-256 hash for a given file.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        None

    """
    file_path = tmp_path / "paper.pdf"
    file_path.write_bytes(b"abc")

    assert sha256_file(file_path) == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_list_and_read_pageindex_cache(tmp_path: Path) -> None:
    """Test retrieving list of manifests and querying page index cache contents.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        None

    """
    document_id = "a" * 64
    document_root = tmp_path / document_id
    document_root.mkdir()
    (document_root / "manifest.json").write_text(
        json.dumps(
            {
                "document_id": document_id,
                "source_path": "raw/papers/teste.pdf",
                "source_filename": "teste.pdf",
                "page_count": 2,
            }
        ),
        encoding="utf-8",
    )
    (document_root / "tree.json").write_text(
        json.dumps(
            {
                "children": [
                    {
                        "page": 1,
                        "title": "Modelo PEARLS",
                        "text": "credito e liquidez",
                    },
                    {"page": 2, "title": "Outro tema", "text": "governanca"},
                ]
            }
        ),
        encoding="utf-8",
    )

    manifests = list_pageindex_manifests(tmp_path)
    cache = read_pageindex_cache(tmp_path, document_id, query="credito", limit=5)

    assert manifests[0]["source_path"] == "raw/papers/teste.pdf"
    assert cache["found"] is True
    assert len(cache["matches"]) == 1
    assert cache["matches"][0]["page"] == 1
    assert "credito" in cache["matches"][0]["excerpt"]


def test_resolve_pdf_cache_by_source_path(tmp_path: Path) -> None:
    """Test resolving a PDF document ID and manifest by its source path.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        None

    """
    vault = tmp_path / "vault"
    raw_papers = vault / "raw" / "papers"
    pageindex_root = vault / ".pageindex"
    raw_papers.mkdir(parents=True)
    pageindex_root.mkdir()
    pdf_path = raw_papers / "teste.pdf"
    pdf_path.write_bytes(b"abc")
    document_id = sha256_file(pdf_path)
    document_root = pageindex_root / document_id
    document_root.mkdir()
    (document_root / "manifest.json").write_text(
        json.dumps({"source_path": "raw/papers/teste.pdf"}),
        encoding="utf-8",
    )

    resolved = resolve_pdf_cache(vault, raw_papers, pageindex_root, "raw/papers/teste.pdf")

    assert resolved["document_id"] == document_id
    assert resolved["cache_found"] is True
    assert resolved["manifest"]["source_path"] == "raw/papers/teste.pdf"


def test_index_pdf_with_command_reports_missing_configuration(tmp_path: Path) -> None:
    """Test PageIndex command bridge reports explicit disabled status.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        None

    """
    vault = tmp_path / "vault"
    raw_papers = vault / "raw" / "papers"
    pageindex_root = vault / ".pageindex"
    raw_papers.mkdir(parents=True)
    pageindex_root.mkdir()
    (raw_papers / "teste.pdf").write_bytes(b"abc")

    result = index_pdf_with_command(
        vault,
        raw_papers,
        pageindex_root,
        "raw/papers/teste.pdf",
        pageindex_command=None,
    )

    assert result["indexed"] is False
    assert "PAGEINDEX_COMMAND" in result["reason"]


def test_index_pdf_with_command_persists_stdout_tree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test external PageIndex bridge persists stdout JSON as tree cache.

    Args:
        tmp_path: Pytest temporary directory fixture.
        monkeypatch: Pytest monkeypatch utility fixture.

    Returns:
        None

    """
    vault = tmp_path / "vault"
    raw_papers = vault / "raw" / "papers"
    pageindex_root = vault / ".pageindex"
    raw_papers.mkdir(parents=True)
    pageindex_root.mkdir()
    pdf_path = raw_papers / "teste.pdf"
    pdf_path.write_bytes(b"abc")

    monkeypatch.setattr("tools_pdf.shutil.which", lambda _command: "fake-pageindex")
    monkeypatch.setattr(
        "tools_pdf.subprocess.run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0,
            stdout='{"nodes": [{"page": 1, "text": "conteudo indexado"}]}',
            stderr="",
        ),
    )

    result = index_pdf_with_command(
        vault,
        raw_papers,
        pageindex_root,
        "raw/papers/teste.pdf",
        pageindex_command="fake-pageindex --json",
    )

    assert result["indexed"] is True
    assert (vault / result["tree_path"]).exists()
    assert result["manifest"]["index_source"] == "pageindex_external_command"


def test_index_pdf_with_command_preserves_windows_command_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test PageIndex bridge preserves Windows absolute executable paths.

    Args:
        tmp_path: Pytest temporary directory fixture.
        monkeypatch: Pytest monkeypatch utility fixture.

    Returns:
        None

    """
    vault = tmp_path / "vault"
    raw_papers = vault / "raw" / "papers"
    pageindex_root = vault / ".pageindex"
    raw_papers.mkdir(parents=True)
    pageindex_root.mkdir()
    (raw_papers / "teste.pdf").write_bytes(b"abc")
    captured: dict[str, list[str]] = {}
    windows_pageindex = r"C:\Users\Nome\.gemini\pageindex"

    monkeypatch.setattr("tools_command.os.name", "nt")
    monkeypatch.setattr("tools_pdf.shutil.which", lambda command: command)

    def fake_run(command: list[str], *_args: object, **_kwargs: object) -> SimpleNamespace:
        captured["command"] = command
        return SimpleNamespace(
            returncode=0,
            stdout='{"nodes": [{"page": 1, "text": "conteudo indexado"}]}',
            stderr="",
        )

    monkeypatch.setattr("tools_pdf.subprocess.run", fake_run)

    result = index_pdf_with_command(
        vault,
        raw_papers,
        pageindex_root,
        "raw/papers/teste.pdf",
        pageindex_command=f"{windows_pageindex} --json",
    )

    assert result["indexed"] is True
    assert captured["command"][:2] == [windows_pageindex, "--json"]


def test_read_pageindex_page_returns_page_text(tmp_path: Path) -> None:
    """Test extracting layout text of a specific page from PageIndex cache tree.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        None

    """
    document_id = "b" * 64
    document_root = tmp_path / document_id
    document_root.mkdir()
    (document_root / "manifest.json").write_text(
        json.dumps({"document_id": document_id, "source_path": "raw/papers/teste.pdf"}),
        encoding="utf-8",
    )
    (document_root / "tree.json").write_text(
        json.dumps(
            {
                "nodes": [
                    {"page": 1, "text": "conteudo da primeira pagina"},
                    {
                        "page": 2,
                        "heading": "Segunda pagina",
                        "content": "conteudo relevante",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    page = read_pageindex_page(tmp_path, document_id, 2)

    assert page["found"] is True
    assert page["page"] == 2
    assert page["node_count"] == 1
    assert "Segunda pagina" in page["text"]
    assert "conteudo relevante" in page["text"]


def test_persist_pageindex_cache_writes_tree_and_manifest(
    tmp_path: Path,
) -> None:
    """Test creating and saving a tree JSON and manifest file for a given PDF.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        None

    """
    vault = tmp_path / "vault"
    raw_papers = vault / "raw" / "papers"
    pageindex_root = vault / ".pageindex"
    raw_papers.mkdir(parents=True)
    pdf_path = raw_papers / "teste.pdf"
    pdf_path.write_bytes(b"abc")

    persisted = persist_pageindex_cache(
        vault,
        raw_papers,
        pageindex_root,
        "raw/papers/teste.pdf",
        {"nodes": [{"page": 3, "text": "conteudo indexado"}]},
    )

    tree_path = vault / persisted["tree_path"]
    manifest_path = vault / persisted["manifest_path"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert tree_path.exists()
    assert manifest_path.exists()
    assert manifest["document_id"] == sha256_file(pdf_path)
    assert manifest["source_path"] == "raw/papers/teste.pdf"
    assert manifest["byte_size"] == 3
    assert manifest["page_count_estimate"] == 3


def test_persist_pageindex_cache_rejects_invalid_tree_json(
    tmp_path: Path,
) -> None:
    """Test that persist_pageindex_cache raises ValueError on malformed tree input.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        None

    """
    vault = tmp_path / "vault"
    raw_papers = vault / "raw" / "papers"
    pageindex_root = vault / ".pageindex"
    raw_papers.mkdir(parents=True)
    (raw_papers / "teste.pdf").write_bytes(b"abc")

    with pytest.raises(ValueError, match="valid JSON"):
        persist_pageindex_cache(
            vault,
            raw_papers,
            pageindex_root,
            "raw/papers/teste.pdf",
            "{invalid",
        )


def test_read_pageindex_cache_rejects_invalid_document_id(
    tmp_path: Path,
) -> None:
    """Test that read_pageindex_cache validates the document ID structure.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        None

    """
    with pytest.raises(ValueError, match="document_id"):
        read_pageindex_cache(tmp_path, "../invalid")


def test_estimate_document_processing(tmp_path: Path) -> None:
    """Test estimating cost, tokens, and pages of a PDF document.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        None

    """
    vault = tmp_path / "vault"
    raw_papers = vault / "raw" / "papers"
    pageindex_root = vault / ".pageindex"
    raw_papers.mkdir(parents=True)
    pageindex_root.mkdir()
    pdf_path = raw_papers / "teste.pdf"
    pdf_path.write_bytes(b"abc")

    estimate = estimate_document_processing(
        vault, raw_papers, pageindex_root, "raw/papers/teste.pdf"
    )

    assert estimate["source_filename"] == "teste.pdf"
    assert estimate["cache_found"] is False
    assert estimate["page_count"] >= 1
    assert "cost_projections" in estimate
    assert "gemini_1_5_flash" in estimate["cost_projections"]
    assert "total_usd" in estimate["cost_projections"]["gemini_1_5_flash"]


def test_index_pdf_with_command_using_docling(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test indexing PDF using Docling parser mode.

    Args:
        tmp_path: Pytest temporary directory fixture.
        monkeypatch: Pytest monkeypatch utility fixture.

    Returns:
        None

    """
    vault = tmp_path / "vault"
    raw_papers = vault / "raw" / "papers"
    pageindex_root = vault / ".pageindex"
    raw_papers.mkdir(parents=True)
    pageindex_root.mkdir()
    pdf_path = raw_papers / "teste.pdf"
    pdf_path.write_bytes(b"abc")

    # Mock docling converter
    class DummyElement:
        def __init__(self, text: str):
            self.text = text

            class DummyProv:
                page_no = 2

            self.prov = [DummyProv()]

    class DummyDocument:
        def __init__(self):
            self.elements = [DummyElement("secao contabilidade"), DummyElement("tabela pearls")]

    class DummyConverter:
        def convert(self, path: str) -> SimpleNamespace:
            return SimpleNamespace(document=DummyDocument())

    monkeypatch.setattr("tools_pdf.HAS_DOCLING", True)
    monkeypatch.setattr("tools_pdf.DocumentConverter", DummyConverter, raising=False)

    result = index_pdf_with_command(
        vault,
        raw_papers,
        pageindex_root,
        "raw/papers/teste.pdf",
        pageindex_command="docling",
        engine="docling",
    )

    assert result["indexed"] is True
    assert (vault / result["tree_path"]).exists()
    assert result["manifest"]["index_source"] == "docling_parser"
    assert result["manifest"]["page_count_estimate"] == 2
