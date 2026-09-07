"""Unit tests for the project configuration loader.

Tests the environment variable parsing, path resolution, and validation logic.
"""

from __future__ import annotations

from pathlib import Path

import pytest

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
    from pydantic import ValidationError
    with pytest.raises(ValidationError, match="Diretorios obrigatorios ausentes ou invalidos"):
        load_settings(env_file)
