"""Configuration manager for the LLM ZettelBrain automation engine.

This module loads, resolves, and validates configuration paths and environment
settings from local system variables and `.env` files.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigError(RuntimeError):
    """Raised when project configuration is missing or invalid.

    Args:
        *args: Variable length argument list passed to RuntimeError.
        **kwargs: Arbitrary keyword arguments passed to RuntimeError.

    """


class Settings(BaseSettings):
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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_empty=True,
    )

    vault_path: Path = Field(default=Path("."), alias="OBSIDIAN_VAULT_PATH")
    ingestion_history_path: Path = Field(
        default=Path(".state/historico_ingestao.txt"), alias="HISTORICO_INGESTAO_PATH"
    )
    raw_articles_path: Path = Field(default=Path("raw/articles"), alias="RAW_ARTICLES_PATH")
    raw_youtube_path: Path = Field(default=Path("raw/youtube"), alias="RAW_YOUTUBE_PATH")
    raw_papers_path: Path = Field(default=Path("raw/papers"), alias="RAW_PAPERS_PATH")
    zettelkasten_path: Path = Field(default=Path("zettelbrain"), alias="ZETTELKASTEN_PATH")
    logs_path: Path = Field(default=Path("logs"), alias="LOGS_PATH")
    youtube_playlist_id: str | None = Field(default=None, alias="YOUTUBE_PLAYLIST_ID")
    qmd_command: str | None = Field(default="qmd", alias="QMD_COMMAND")
    pageindex_command: str | None = Field(default=None, alias="PAGEINDEX_COMMAND")
    llm_model_name: str = Field(default="gemini-2.5-pro", alias="LLM_MODEL_NAME")
    embedding_provider: str = Field(default="hashing", alias="EMBEDDING_PROVIDER")
    embedding_model_name: str = Field(default="nomic-embed-text", alias="EMBEDDING_MODEL_NAME")
    embedding_endpoint: str | None = Field(
        default="http://localhost:11434/api/embeddings", alias="EMBEDDING_ENDPOINT"
    )
    embedding_index_path: Path = Field(
        default=Path(".state/embeddings_index.json"), alias="EMBEDDING_INDEX_PATH"
    )
    embedding_dimensions: int = Field(default=256, alias="EMBEDDING_DIMENSIONS", gt=0)

    @model_validator(mode="after")
    def resolve_paths_and_validate(self) -> Settings:
        """Resolve paths against vault_path and validate provider specifics.

        Returns:
            Settings: The validated instance.
            
        Raises:
            ValueError: If mandatory directories are missing or embedding provider 
                configuration is invalid.

        """
        # 1. Resolve vault_path to absolute
        repo_root = Path(__file__).resolve().parents[1]
        self.vault_path = self.vault_path.expanduser()
        if not self.vault_path.is_absolute():
            self.vault_path = repo_root / self.vault_path
        self.vault_path = self.vault_path.resolve()

        # 2. Helper to resolve other paths against vault_path
        def _resolve(path: Path) -> Path:
            path = path.expanduser()
            if not path.is_absolute():
                path = self.vault_path / path
            return path.resolve()

        self.ingestion_history_path = _resolve(self.ingestion_history_path)
        self.raw_articles_path = _resolve(self.raw_articles_path)
        self.raw_youtube_path = _resolve(self.raw_youtube_path)
        self.raw_papers_path = _resolve(self.raw_papers_path)
        self.zettelkasten_path = _resolve(self.zettelkasten_path)
        self.logs_path = _resolve(self.logs_path)
        self.embedding_index_path = _resolve(self.embedding_index_path)

        # 3. Check for existence of mandatory paths
        required_dirs = {
            "OBSIDIAN_VAULT_PATH": self.vault_path,
            "RAW_ARTICLES_PATH": self.raw_articles_path,
            "RAW_YOUTUBE_PATH": self.raw_youtube_path,
            "RAW_PAPERS_PATH": self.raw_papers_path,
            "ZETTELKASTEN_PATH": self.zettelkasten_path,
        }
        missing = [name for name, path in required_dirs.items() if not path.exists()]
        if missing:
            raise ValueError(f"Diretorios obrigatorios ausentes ou invalidos: {', '.join(missing)}")

        # 4. Clean strings
        self.embedding_provider = self.embedding_provider.strip().lower()

        # 5. Validate provider
        if self.embedding_provider not in {"hashing", "ollama"}:
            raise ValueError("EMBEDDING_PROVIDER deve ser 'hashing' ou 'ollama'.")
        if self.embedding_provider == "ollama" and not self.embedding_endpoint:
            raise ValueError("EMBEDDING_ENDPOINT e obrigatorio para EMBEDDING_PROVIDER=ollama.")

        return self


def load_settings(env_path: Path | str | None = None, *, require_youtube: bool = False) -> Settings:
    """Load project settings from .env and environment variables.

    Args:
        env_path: Path to the .env file. If None, it defaults to the repo root's .env file.
        require_youtube: If True, validation will fail if YOUTUBE_PLAYLIST_ID is missing.

    Returns:
        Settings: The loaded and validated Settings object.

    Raises:
        ConfigError: If YouTube settings are required but missing.
        ValueError: If paths or other variables are invalid.

    """
    repo_root = Path(__file__).resolve().parents[1]
    dotenv_path = Path(env_path) if env_path else repo_root / ".env"

    settings = Settings(_env_file=dotenv_path) if dotenv_path.exists() else Settings()

    if require_youtube and not settings.youtube_playlist_id:
        raise ConfigError("YOUTUBE_PLAYLIST_ID e obrigatorio para o ETL do YouTube.")

    return settings

