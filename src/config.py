"""Configuration manager for the LLM ZettelBrain automation engine.

This module loads, resolves, and validates configuration paths and environment
settings from local system variables and `.env` files.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


class ConfigError(RuntimeError):
    """Raised when project configuration is missing or invalid.

    Args:
        *args: Variable length argument list passed to RuntimeError.
        **kwargs: Arbitrary keyword arguments passed to RuntimeError.

    """


@dataclass(frozen=True)
class Settings:
    """Project-wide settings loaded from environment and config.

    Attributes:
        vault_path: Path to the Obsidian vault.
        ingestion_history_path: Path to the file containing ingested video IDs.
        raw_articles_path: Path to raw Markdown articles.
        raw_youtube_path: Path to raw YouTube transcripts.
        raw_papers_path: Path to raw academic papers (PDFs).
        zettelkasten_path: Path to the ZettelBrain folder.
        logs_path: Path where log files are written.
        youtube_playlist_id: ID of the YouTube playlist for the ETL pipeline.
        qmd_command: Name of/path to the qmd CLI executable.
        pageindex_command: Optional external command that indexes a PDF and prints tree JSON.
        llm_model_name: Name of the default LLM model to be used.
        embedding_provider: Embedding backend name, such as hashing or ollama.
        embedding_model_name: Name of the default embedding model.
        embedding_endpoint: Local embedding endpoint URL, when provider needs one.
        embedding_index_path: Path to the local embedding index JSON file.
        embedding_dimensions: Number of dimensions in the local embedding vector.

    """

    vault_path: Path
    ingestion_history_path: Path
    raw_articles_path: Path
    raw_youtube_path: Path
    raw_papers_path: Path
    zettelkasten_path: Path
    logs_path: Path
    youtube_playlist_id: str | None
    qmd_command: str | None
    pageindex_command: str | None
    llm_model_name: str
    embedding_provider: str
    embedding_model_name: str
    embedding_endpoint: str | None
    embedding_index_path: Path
    embedding_dimensions: int


def load_settings(env_path: Path | str | None = None, *, require_youtube: bool = False) -> Settings:
    """Load project settings from .env and environment variables.

    Args:
        env_path: Path to the .env file. If None, it defaults to the repo root's .env file.
        require_youtube: If True, validation will fail if YOUTUBE_PLAYLIST_ID is missing.

    Returns:
        Settings: The loaded and validated Settings object.

    Raises:
        ConfigError: If mandatory directories are missing or if YouTube settings are
            required but missing.

    """
    repo_root = Path(__file__).resolve().parents[1]
    dotenv_path = Path(env_path) if env_path else repo_root / ".env"
    _load_dotenv(dotenv_path)

    vault_path = _resolve_path(os.getenv("OBSIDIAN_VAULT_PATH", "."), repo_root)
    settings = Settings(
        vault_path=vault_path,
        ingestion_history_path=_resolve_path(
            os.getenv("HISTORICO_INGESTAO_PATH", ".state/historico_ingestao.txt"),
            vault_path,
        ),
        raw_articles_path=_resolve_path(os.getenv("RAW_ARTICLES_PATH", "raw/articles"), vault_path),
        raw_youtube_path=_resolve_path(os.getenv("RAW_YOUTUBE_PATH", "raw/youtube"), vault_path),
        raw_papers_path=_resolve_path(os.getenv("RAW_PAPERS_PATH", "raw/papers"), vault_path),
        zettelkasten_path=_resolve_path(os.getenv("ZETTELKASTEN_PATH", "zettelbrain"), vault_path),
        logs_path=_resolve_path(os.getenv("LOGS_PATH", "logs"), vault_path),
        youtube_playlist_id=_empty_to_none(os.getenv("YOUTUBE_PLAYLIST_ID")),
        qmd_command=_empty_to_none(os.getenv("QMD_COMMAND", "qmd")),
        pageindex_command=_empty_to_none(os.getenv("PAGEINDEX_COMMAND")),
        llm_model_name=os.getenv("LLM_MODEL_NAME", "gemini-2.5-pro"),
        embedding_provider=os.getenv("EMBEDDING_PROVIDER", "hashing").strip().lower(),
        embedding_model_name=os.getenv("EMBEDDING_MODEL_NAME", "nomic-embed-text"),
        embedding_endpoint=_empty_to_none(
            os.getenv("EMBEDDING_ENDPOINT", "http://localhost:11434/api/embeddings")
        ),
        embedding_index_path=_resolve_path(
            os.getenv("EMBEDDING_INDEX_PATH", ".state/embeddings_index.json"),
            vault_path,
        ),
        embedding_dimensions=_parse_positive_int(os.getenv("EMBEDDING_DIMENSIONS", "256")),
    )
    _validate_settings(settings, require_youtube=require_youtube)
    return settings


def _load_dotenv(dotenv_path: Path) -> None:
    """Load environment variables from the specified .env path using dotenv.

    If dotenv is not installed, it falls back to a custom parser.

    Args:
        dotenv_path: Absolute path to the .env file.

    Returns:
        None

    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        _load_dotenv_fallback(dotenv_path)
        return

    if dotenv_path.exists():
        load_dotenv(dotenv_path, override=False)


def _load_dotenv_fallback(dotenv_path: Path) -> None:
    """Fall back to a simple manual parser if python-dotenv is not installed.

    Args:
        dotenv_path: Absolute path to the .env file.

    Returns:
        None

    """
    if not dotenv_path.exists():
        return

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _resolve_path(value: str, base_path: Path) -> Path:
    """Resolve a path string relative to a base path if it is not absolute.

    Args:
        value: The path string to resolve.
        base_path: The base Path to resolve against if the path is relative.

    Returns:
        Path: The resolved absolute Path object.

    """
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = base_path / path
    return path.resolve()


def _empty_to_none(value: str | None) -> str | None:
    """Convert an empty or whitespace-only string to None.

    Args:
        value: The string to convert.

    Returns:
        str | None: The stripped string, or None if it was empty or whitespace-only.

    """
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _parse_positive_int(value: str | None) -> int:
    """Parse a positive integer environment value.

    Args:
        value: The string representation of the integer to parse.

    Returns:
        int: The parsed positive integer.

    Raises:
        ConfigError: If the value is not a valid integer or is less than or equal to zero.

    """
    try:
        parsed = int(value or "0")
    except ValueError as exc:
        raise ConfigError("EMBEDDING_DIMENSIONS deve ser um inteiro positivo.") from exc
    if parsed <= 0:
        raise ConfigError("EMBEDDING_DIMENSIONS deve ser um inteiro positivo.")
    return parsed


def _validate_settings(settings: Settings, *, require_youtube: bool) -> None:
    """Validate that required paths exist and check for YouTube config if required.

    Args:
        settings: The Settings instance to validate.
        require_youtube: True if youtube configuration must be present.

    Returns:
        None

    Raises:
        ConfigError: If any required path does not exist, or if YouTube settings
            are required but not configured.

    """
    required_dirs = {
        "OBSIDIAN_VAULT_PATH": settings.vault_path,
        "RAW_ARTICLES_PATH": settings.raw_articles_path,
        "RAW_YOUTUBE_PATH": settings.raw_youtube_path,
        "RAW_PAPERS_PATH": settings.raw_papers_path,
        "ZETTELKASTEN_PATH": settings.zettelkasten_path,
    }

    missing = [name for name, path in required_dirs.items() if not path.exists()]
    if missing:
        joined = ", ".join(missing)
        raise ConfigError(f"Diretorios obrigatorios ausentes ou invalidos: {joined}")

    if require_youtube and not settings.youtube_playlist_id:
        raise ConfigError("YOUTUBE_PLAYLIST_ID e obrigatorio para o ETL do YouTube.")

    if settings.embedding_provider not in {"hashing", "ollama"}:
        raise ConfigError("EMBEDDING_PROVIDER deve ser 'hashing' ou 'ollama'.")

    if settings.embedding_provider == "ollama" and not settings.embedding_endpoint:
        raise ConfigError("EMBEDDING_ENDPOINT e obrigatorio para EMBEDDING_PROVIDER=ollama.")
