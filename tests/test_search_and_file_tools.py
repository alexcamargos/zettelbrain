"""Unit tests for file-level retrieval and search utilities.

Tests lexical keyword search, qmd executable checks, subprocess result parsing,
and file path safety validation.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from tools_command import split_command
from tools_file import list_markdown_files, read_markdown_file, write_markdown_file
from tools_search import (
    SearchResult,
    hybrid_search,
    lexical_search,
    merge_search_results,
    qmd_search,
    retrieval_status,
)


def test_split_command_preserves_windows_absolute_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test Windows command parsing keeps backslash path separators intact.

    Args:
        monkeypatch: Pytest monkeypatch utility fixture.

    Returns:
        None
    """
    monkeypatch.setattr("tools_command.os.name", "nt")

    assert split_command(r"C:\Users\Nome\.gemini\qmd --json") == [
        r"C:\Users\Nome\.gemini\qmd",
        "--json",
    ]
    assert split_command(r'"C:\Program Files\qmd.exe" --json') == [
        r"C:\Program Files\qmd.exe",
        "--json",
    ]


def test_split_command_keeps_posix_shell_quoting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test POSIX command parsing remains compatible with quoted arguments.

    Args:
        monkeypatch: Pytest monkeypatch utility fixture.

    Returns:
        None
    """
    monkeypatch.setattr("tools_command.os.name", "posix")

    assert split_command("qmd --label 'two words'") == ["qmd", "--label", "two words"]


def test_lexical_search_returns_ranked_results(tmp_path: Path) -> None:
    """Test that lexical_search returns correctly ranked search results by density.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        None
    """
    (tmp_path / "a.md").write_text("credito credito risco", encoding="utf-8")
    (tmp_path / "b.md").write_text("risco operacional", encoding="utf-8")

    results = lexical_search(tmp_path, "credito risco")

    assert [result.path for result in results] == ["a.md", "b.md"]
    assert results[0].score > results[1].score
    assert results[0].engine == "bm25"


def test_hybrid_search_falls_back_to_lexical_when_qmd_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that hybrid_search falls back to lexical search if qmd is missing.

    Args:
        tmp_path: Pytest temporary directory fixture.
        monkeypatch: Pytest monkeypatch utility fixture.

    Returns:
        None
    """
    (tmp_path / "a.md").write_text("credito risco", encoding="utf-8")
    monkeypatch.setattr("tools_search.shutil.which", lambda _command: None)

    results = hybrid_search(tmp_path, "credito", qmd_command="qmd")

    assert len(results) == 1
    assert results[0].engine == "bm25"


def test_retrieval_status_reports_missing_qmd(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test retrieval_status exposes qmd availability and fallback engine.

    Args:
        monkeypatch: Pytest monkeypatch utility fixture.

    Returns:
        None
    """
    monkeypatch.setattr("tools_search.shutil.which", lambda _command: None)

    status = retrieval_status("qmd")

    assert status.qmd_configured is True
    assert status.qmd_available is False
    assert status.fallback_engine == "bm25"


def test_qmd_search_parses_stdout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that qmd_search runs qmd command and parses stdout correctly.

    Args:
        tmp_path: Pytest temporary directory fixture.
        monkeypatch: Pytest monkeypatch utility fixture.

    Returns:
        None
    """
    (tmp_path / "a.md").write_text("conteudo", encoding="utf-8")
    monkeypatch.setattr("tools_search.shutil.which", lambda _command: "qmd")
    monkeypatch.setattr(
        "tools_search.subprocess.run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0,
            stdout="a.md: trecho encontrado\n",
        ),
    )

    results = qmd_search(tmp_path, "credito", qmd_command="qmd")

    assert len(results) == 1
    assert results[0].path == "a.md"
    assert results[0].engine == "qmd"


def test_qmd_search_preserves_windows_command_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test qmd_search preserves Windows absolute executable paths.

    Args:
        tmp_path: Pytest temporary directory fixture.
        monkeypatch: Pytest monkeypatch utility fixture.

    Returns:
        None
    """
    captured: dict[str, list[str]] = {}
    windows_qmd = r"C:\Users\Nome\.gemini\qmd"

    monkeypatch.setattr("tools_command.os.name", "nt")
    monkeypatch.setattr("tools_search.shutil.which", lambda command: command)

    def fake_run(command: list[str], *_args: object, **_kwargs: object) -> SimpleNamespace:
        captured["command"] = command
        return SimpleNamespace(returncode=0, stdout="a.md: trecho encontrado\n")

    monkeypatch.setattr("tools_search.subprocess.run", fake_run)

    qmd_search(tmp_path, "credito", qmd_command=f"{windows_qmd} --profile local")

    assert captured["command"][:3] == [windows_qmd, "--profile", "local"]


def test_qmd_search_parses_windows_absolute_stdout_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test qmd_search parses absolute Windows output paths without breaking on drive letters."""
    note_path = tmp_path / "nested" / "a.md"
    note_path.parent.mkdir()
    note_path.write_text("conteudo", encoding="utf-8")
    stdout_line = f"{note_path}: trecho encontrado\n"

    monkeypatch.setattr("tools_search.shutil.which", lambda _command: "qmd")
    monkeypatch.setattr(
        "tools_search.subprocess.run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0,
            stdout=stdout_line,
        ),
    )

    results = qmd_search(tmp_path, "credito", qmd_command="qmd")

    assert len(results) == 1
    assert results[0].path == "nested/a.md"
    assert results[0].excerpt == "trecho encontrado"


def test_file_tools_are_limited_to_markdown_inside_root(tmp_path: Path) -> None:
    """Test that file listing and reading are constrained within root.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        None
    """
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "note.md").write_text("conteudo", encoding="utf-8")
    (tmp_path / "note.txt").write_text("bloqueado", encoding="utf-8")

    assert list_markdown_files(tmp_path) == ["nested/note.md"]
    assert read_markdown_file(tmp_path, "nested/note.md") == "conteudo"

    with pytest.raises(ValueError):
        read_markdown_file(tmp_path, "note.txt")


def test_merge_search_results_deduplicates_and_combines_engines() -> None:
    """Test local hybrid result merging combines scores and engine labels.

    Returns:
        None
    """
    merged = merge_search_results(
        [
            SearchResult(
                path="a.md",
                score=1.5,
                excerpt="credito",
                engine="bm25",
            )
        ],
        [
            SearchResult(
                path="a.md",
                score=0.5,
                excerpt="risco",
                engine="hash-embedding",
            ),
            SearchResult(
                path="b.md",
                score=0.7,
                excerpt="pearls",
                engine="hash-embedding",
            ),
        ],
        limit=2,
    )

    assert [result.path for result in merged] == ["a.md", "b.md"]
    assert merged[0].score == 2.0
    assert merged[0].engine == "bm25+hash-embedding"


def test_write_markdown_file_creates_and_edits_safely(tmp_path: Path) -> None:
    """Test that writing markdown files is constrained to root and suffix constraints.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        None
    """
    rel_path = "nested/new_note.md"
    written = write_markdown_file(tmp_path, rel_path, "conteudo nota")
    assert written == "nested/new_note.md"
    assert (tmp_path / "nested" / "new_note.md").read_text(encoding="utf-8") == "conteudo nota"

    with pytest.raises(ValueError, match="Apenas arquivos Markdown"):
        write_markdown_file(tmp_path, "nested/new_note.txt", "conteudo")

    with pytest.raises(ValueError, match="Caminho fora do cofre"):
        write_markdown_file(tmp_path, "../outside.md", "escape")

