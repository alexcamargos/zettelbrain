"""Helper functions for safe file discovery and reading within a directory tree.

Provides functions to list markdown files and retrieve their contents while
guaranteeing directory boundary validation.
"""

from __future__ import annotations

from pathlib import Path


def list_markdown_files(root: Path) -> list[str]:
    """Recursively list all markdown files relative to a root directory.

    Args:
        root: The root folder Path to scan for files.

    Returns:
        list[str]: Sorted list of forward-slash relative path strings.
    """
    return sorted(str(path.relative_to(root)).replace("\\", "/") for path in root.rglob("*.md"))


def read_markdown_file(root: Path, relative_path: str) -> str:
    """Read the UTF-8 content of a markdown file inside a root directory safely.

    Args:
        root: The root folder Path containing the target file.
        relative_path: The relative path to the markdown file to read.

    Returns:
        str: Text content of the file.

    Raises:
        ValueError: If the file is not a markdown file (.md).
    """
    target = _safe_child(root, relative_path)
    if target.suffix.lower() != ".md":
        raise ValueError("Apenas arquivos Markdown podem ser lidos por esta ferramenta.")
    return target.read_text(encoding="utf-8")


def _safe_child(root: Path, relative_path: str) -> Path:
    """Resolve child path and verify it stays inside root boundaries.

    Args:
        root: The base parent folder Path.
        relative_path: The relative path to resolve.

    Returns:
        Path: The resolved absolute Path object.

    Raises:
        ValueError: If the path escapes the root directory.
        FileNotFoundError: If the file does not exist or is not a file.
    """
    resolved_root = root.resolve()
    target = (resolved_root / relative_path).resolve()
    if resolved_root != target and resolved_root not in target.parents:
        raise ValueError("Caminho fora do cofre bloqueado.")
    if not target.exists() or not target.is_file():
        raise FileNotFoundError(relative_path)
    return target


def write_markdown_file(root: Path, relative_path: str, content: str) -> str:
    """Write the UTF-8 content to a markdown file inside a root directory safely.

    Args:
        root: The root folder Path containing the target file.
        relative_path: The relative path to the markdown file to write.
        content: The text content to write.

    Returns:
        str: Relative path of the written file.

    Raises:
        ValueError: If the file is not a markdown file (.md) or escapes boundaries.
    """
    resolved_root = root.resolve()
    target = (resolved_root / relative_path).resolve()
    if resolved_root != target and resolved_root not in target.parents:
        raise ValueError("Caminho fora do cofre bloqueado.")
    if target.suffix.lower() != ".md":
        raise ValueError("Apenas arquivos Markdown (.md) podem ser criados ou editados.")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8", newline="\n")
    return str(target.relative_to(resolved_root)).replace("\\", "/")

