"""Unit tests for the project configuration loader.

Tests the environment variable parsing, path resolution, and validation logic.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from config import ConfigError, load_settings


def test_load_settings_from_env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that settings are correctly loaded from a valid .env configuration file.

    Args:
        tmp_path: Pytest temporary directory fixture.
        monkeypatch: Pytest monkeypatch utility fixture.

    Returns:
        None

    """
    (tmp_path / "raw" / "articles").mkdir(parents=True)
    (tmp_path / "raw" / "youtube").mkdir(parents=True)
    (tmp_path / "raw" / "papers").mkdir(parents=True)
    (tmp_path / "zettelbrain").mkdir()
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                f"OBSIDIAN_VAULT_PATH={tmp_path}",
                "YOUTUBE_PLAYLIST_ID=PL_TESTE",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("OBSIDIAN_VAULT_PATH", raising=False)
    monkeypatch.delenv("YOUTUBE_PLAYLIST_ID", raising=False)

    settings = load_settings(env_file, require_youtube=True)

    assert settings.vault_path == tmp_path.resolve()
    assert settings.youtube_playlist_id == "PL_TESTE"
    assert settings.raw_articles_path == (tmp_path / "raw" / "articles").resolve()
    assert settings.raw_youtube_path == (tmp_path / "raw" / "youtube").resolve()
    assert settings.pageindex_command is None
    assert settings.embedding_provider == "hashing"
    assert settings.embedding_endpoint == "http://localhost:11434/api/embeddings"
    assert settings.embedding_index_path == (tmp_path / ".state" / "embeddings_index.json")
    assert settings.embedding_dimensions == 256
    assert settings.log_level == "INFO"
    assert settings.log_rotation == "10 MB"
    assert settings.log_retention == "14 days"
    assert settings.article_fetch_max_attempts == 2
    assert settings.article_fetch_retry_delay_seconds == 30
    assert settings.embedding_timeout_seconds == 20
    assert settings.qmd_timeout_seconds == 20
    assert settings.pageindex_timeout_seconds == 120
    assert settings.search_default_limit == 8


def test_load_settings_custom_operational_fields(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that custom operational and logging settings are parsed correctly.

    Args:
        tmp_path: Pytest temporary directory fixture.
        monkeypatch: Pytest monkeypatch utility fixture.

    Returns:
        None

    """
    (tmp_path / "raw" / "articles").mkdir(parents=True)
    (tmp_path / "raw" / "youtube").mkdir(parents=True)
    (tmp_path / "raw" / "papers").mkdir(parents=True)
    (tmp_path / "zettelbrain").mkdir()
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                f"OBSIDIAN_VAULT_PATH={tmp_path}",
                "LOG_LEVEL=debug",
                "LOG_ROTATION=20 MB",
                "LOG_RETENTION=30 days",
                "ARTICLE_FETCH_MAX_ATTEMPTS=5",
                "ARTICLE_FETCH_RETRY_DELAY_SECONDS=10",
                "EMBEDDING_TIMEOUT_SECONDS=45",
                "QMD_TIMEOUT_SECONDS=30",
                "PAGEINDEX_TIMEOUT_SECONDS=180",
                "SEARCH_DEFAULT_LIMIT=15",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("OBSIDIAN_VAULT_PATH", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)

    settings = load_settings(env_file)

    assert settings.log_level == "DEBUG"
    assert settings.log_rotation == "20 MB"
    assert settings.log_retention == "30 days"
    assert settings.article_fetch_max_attempts == 5
    assert settings.article_fetch_retry_delay_seconds == 10
    assert settings.embedding_timeout_seconds == 45
    assert settings.qmd_timeout_seconds == 30
    assert settings.pageindex_timeout_seconds == 180
    assert settings.search_default_limit == 15


def test_load_settings_raises_value_error_on_invalid_log_level(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that ValidationError is raised if LOG_LEVEL is invalid.

    Args:
        tmp_path: Pytest temporary directory fixture.
        monkeypatch: Pytest monkeypatch utility fixture.

    Returns:
        None

    """
    (tmp_path / "raw" / "articles").mkdir(parents=True)
    (tmp_path / "raw" / "youtube").mkdir(parents=True)
    (tmp_path / "raw" / "papers").mkdir(parents=True)
    (tmp_path / "zettelbrain").mkdir()
    env_file = tmp_path / ".env"
    env_file.write_text(
        f"OBSIDIAN_VAULT_PATH={tmp_path}\nLOG_LEVEL=VERBOSE\n", encoding="utf-8"
    )
    monkeypatch.delenv("OBSIDIAN_VAULT_PATH", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)

    with pytest.raises(ValidationError, match="LOG_LEVEL deve ser um dos seguintes"):
        load_settings(env_file)


def test_load_settings_raises_value_error_on_invalid_numeric_limits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that ValidationError is raised when numeric bounds (gt=0) are violated.

    Args:
        tmp_path: Pytest temporary directory fixture.
        monkeypatch: Pytest monkeypatch utility fixture.

    Returns:
        None

    """
    (tmp_path / "raw" / "articles").mkdir(parents=True)
    (tmp_path / "raw" / "youtube").mkdir(parents=True)
    (tmp_path / "raw" / "papers").mkdir(parents=True)
    (tmp_path / "zettelbrain").mkdir()
    env_file = tmp_path / ".env"
    env_file.write_text(
        f"OBSIDIAN_VAULT_PATH={tmp_path}\nSEARCH_DEFAULT_LIMIT=0\n", encoding="utf-8"
    )
    monkeypatch.delenv("OBSIDIAN_VAULT_PATH", raising=False)
    monkeypatch.delenv("SEARCH_DEFAULT_LIMIT", raising=False)

    with pytest.raises(ValidationError):
        load_settings(env_file)


def test_load_settings_requires_youtube_when_requested(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that ConfigError is raised if YouTube playlist ID is missing but required.

    Args:
        tmp_path: Pytest temporary directory fixture.
        monkeypatch: Pytest monkeypatch utility fixture.

    Returns:
        None

    """
    (tmp_path / "raw" / "articles").mkdir(parents=True)
    (tmp_path / "raw" / "youtube").mkdir(parents=True)
    (tmp_path / "raw" / "papers").mkdir(parents=True)
    (tmp_path / "zettelbrain").mkdir()
    env_file = tmp_path / ".env"
    env_file.write_text(f"OBSIDIAN_VAULT_PATH={tmp_path}\n", encoding="utf-8")
    monkeypatch.delenv("YOUTUBE_PLAYLIST_ID", raising=False)

    with pytest.raises(ConfigError, match="YOUTUBE_PLAYLIST_ID"):
        load_settings(env_file, require_youtube=True)


def test_load_settings_raises_value_error_on_missing_dirs(tmp_path: Path) -> None:
    """Test that ValueError is raised if mandatory directories are missing.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        None

    """
    env_file = tmp_path / ".env"
    env_file.write_text(f"OBSIDIAN_VAULT_PATH={tmp_path}\n", encoding="utf-8")
    
    # Do not create the expected raw/articles directories
    
    # We expect a pydantic.ValidationError (which wraps the ValueError raised in the validator)
    with pytest.raises(ValidationError, match="Diretorios obrigatorios ausentes ou invalidos"):
        load_settings(env_file)
