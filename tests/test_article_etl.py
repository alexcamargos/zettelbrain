"""Unit tests for the web article ETL pipeline.

This module tests web article downloading, content extraction, slugification,
and saving to markdown format with correct metadata and YAML front matter.
"""

from __future__ import annotations

import json
import urllib.error
from pathlib import Path
from typing import Any

import pytest
from pytest_mock import MockerFixture

from ingestion.article_etl import (
    fetch_and_clean_article,
    fetch_and_clean_article_with_retry,
    save_raw_article,
    slugify,
)


class MockMetaData:
    """Mock class to simulate trafilatura's MetaData object.

    Attributes:
        title: Title of the article.
        author: Author of the article.
        date: Publication date of the article.

    """

    def __init__(self, title: str, author: str, date: str) -> None:
        """Initialize MockMetaData.

        Args:
            title: Title of the article.
            author: Author of the article.
            date: Publication date of the article.

        """
        self.title = title
        self.author = author
        self.date = date


def test_slugify() -> None:
    """Tests that slugify converts arbitrary text to filesystem-safe slugs.

    Returns:
        None

    """
    assert slugify("Meu Artigo Especial! 123") == "meu-artigo-especial-123"
    assert slugify("Python -- Ingestion ETL") == "python-ingestion-etl"
    assert slugify("", default="article") == "article"
    assert slugify("") == ""


def test_fetch_and_clean_article_success(mocker: Any) -> None:
    """Tests successful retrieval and extraction of article content.

    Args:
        mocker: The pytest-mock fixture.

    Returns:
        None

    """
    mocker.patch("trafilatura.fetch_url", return_value="<html>HTML de Teste</html>")
    mocker.patch(
        "trafilatura.extract_metadata",
        return_value=MockMetaData("Título de Teste", "Autor de Teste", "2026-06-06"),
    )
    mocker.patch("trafilatura.extract", return_value="Corpo de texto do artigo.")

    result = fetch_and_clean_article("https://example.com/artigo")

    assert result is not None
    assert result["title"] == "Título de Teste"
    assert result["author"] == "Autor de Teste"
    assert result["date"] == "2026-06-06"
    assert result["url"] == "https://example.com/artigo"
    assert result["content"] == "Corpo de texto do artigo."


def test_fetch_and_clean_article_fetch_failure(mocker: Any) -> None:
    """Tests fetch_and_clean_article returns None when download fails.

    Args:
        mocker: The pytest-mock fixture.

    Returns:
        None

    """
    mocker.patch("trafilatura.fetch_url", return_value=None)

    result = fetch_and_clean_article("https://example.com/artigo")

    assert result is None


def test_fetch_and_clean_article_extraction_failure(mocker: Any) -> None:
    """Tests fetch_and_clean_article returns None when parsing/extracting fails.

    Args:
        mocker: The pytest-mock fixture.

    Returns:
        None

    """
    mocker.patch("trafilatura.fetch_url", return_value="<html>HTML</html>")
    mocker.patch("trafilatura.extract", return_value=None)

    result = fetch_and_clean_article("https://example.com/artigo")

    assert result is None


def test_fetch_and_clean_article_empty_url_raises_error() -> None:
    """Tests that an empty URL raises ValueError.

    Returns:
        None

    Raises:
        ValueError: When the URL is empty.

    """
    with pytest.raises(ValueError, match="Article URL cannot be empty."):
        fetch_and_clean_article("   ")


def test_save_raw_article_success(mocker: Any, tmp_path: Path) -> None:
    """Tests that save_raw_article correctly formats and writes content to disk.

    Args:
        mocker: The pytest-mock fixture.
        tmp_path: Pytest temporary directory fixture.

    Returns:
        None

    """
    mocker.patch(
        "ingestion.article_etl.fetch_and_clean_article",
        return_value={
            "title": "Título Especial",
            "author": "Autor Anônimo",
            "date": "2026-06-06",
            "url": "https://example.com/artigo",
            "content": "Conteúdo limpo do artigo.",
        },
    )

    output = save_raw_article("https://example.com/artigo", tmp_path)

    assert output is not None
    assert output.name == "web-titulo-especial.md"
    assert output.exists()

    content = output.read_text(encoding="utf-8")
    assert 'title: "Título Especial"' in content
    assert 'author: "Autor Anônimo"' in content
    assert 'published_at: "2026-06-06"' in content
    assert 'url: "https://example.com/artigo"' in content
    assert "source_kind: web_article" in content
    assert "Conteúdo limpo do artigo." in content


def test_save_raw_article_custom_filename(mocker: Any, tmp_path: Path) -> None:
    """Tests save_raw_article with custom filename.

    Args:
        mocker: The pytest-mock fixture.
        tmp_path: Pytest temporary directory fixture.

    Returns:
        None

    """
    mocker.patch(
        "ingestion.article_etl.fetch_and_clean_article",
        return_value={
            "title": "Título",
            "author": "Autor",
            "date": "2026",
            "url": "https://example.com/artigo",
            "content": "Conteúdo",
        },
    )

    output = save_raw_article("https://example.com/artigo", tmp_path, filename="custom")

    assert output is not None
    assert output.name == "custom.md"
    assert output.exists()


def test_save_raw_article_failure(mocker: Any, tmp_path: Path) -> None:
    """Tests save_raw_article returns None when fetch_and_clean_article fails.

    Args:
        mocker: The pytest-mock fixture.
        tmp_path: Pytest temporary directory fixture.

    Returns:
        None

    """
    mocker.patch("ingestion.article_etl.fetch_and_clean_article", return_value=None)

    output = save_raw_article("https://example.com/artigo", tmp_path)

    assert output is None


def test_fetch_and_clean_article_with_retry_retries_then_succeeds(mocker: MockerFixture) -> None:
    """Tests access retry waits and succeeds on a second attempt."""
    attempts = {"count": 0}

    def fake_fetch(url: str) -> dict[str, Any] | None:
        attempts["count"] += 1
        if attempts["count"] == 1:
            return None
        return {
            "title": "Título",
            "author": "Autor",
            "date": "2026-06-07",
            "url": url,
            "content": "Conteúdo",
        }

    mocker.patch("ingestion.article_etl.fetch_and_clean_article", side_effect=fake_fetch)
    sleeper = mocker.Mock()

    result = fetch_and_clean_article_with_retry(
        "https://example.com/artigo",
        retry_delay_seconds=30,
        sleep_func=sleeper,
    )

    assert result is not None
    assert attempts["count"] == 2
    sleeper.assert_called_once_with(30)


def test_fetch_and_clean_article_with_retry_records_failure_after_second_attempt(
    mocker: MockerFixture,
    tmp_path: Path,
) -> None:
    """Tests persistent access failure is written to the deferred retry log."""
    mocker.patch("ingestion.article_etl.fetch_and_clean_article", return_value=None)
    sleeper = mocker.Mock()
    error_log_path = tmp_path / "logs" / "article_access_errors.jsonl"

    result = fetch_and_clean_article_with_retry(
        "https://example.com/artigo",
        retry_delay_seconds=30,
        access_error_log_path=error_log_path,
        sleep_func=sleeper,
    )

    assert result is None
    sleeper.assert_called_once_with(30)
    entries = error_log_path.read_text(encoding="utf-8").splitlines()
    assert len(entries) == 1
    payload = json.loads(entries[0])
    assert payload["url"] == "https://example.com/artigo"
    assert payload["attempts"] == 2
    assert payload["error"] == "download_failed_or_remote_content_unavailable"


def test_main_returns_success_exit_code(mocker: MockerFixture, tmp_path: Path) -> None:
    """Tests CLI exits with code 0 when article ingestion succeeds."""
    mocker.patch(
        "sys.argv",
        ["article_etl.py", "--url", "https://example.com/artigo"],
    )
    settings = mocker.Mock(raw_articles_path=tmp_path, logs_path=tmp_path / "logs")
    mocker.patch("ingestion.article_etl.load_settings", return_value=settings)
    mocker.patch("ingestion.article_etl.configure_logging")
    save_raw_article_mock = mocker.patch(
        "ingestion.article_etl.save_raw_article",
        return_value=tmp_path / "web-artigo.md",
    )
    mock_logger = mocker.Mock()
    mocker.patch("ingestion.article_etl.get_logger", return_value=mock_logger)

    from ingestion.article_etl import main

    with pytest.raises(SystemExit) as excinfo:
        main()

    assert excinfo.value.code == 0
    mock_logger.info.assert_called_with("Article ETL completed successfully.")
    save_raw_article_mock.assert_called_once_with(
        url="https://example.com/artigo",
        raw_articles_path=tmp_path,
        filename=None,
        retry_delay_seconds=30,
        access_error_log_path=tmp_path / "logs" / "article_access_errors.jsonl",
    )


def test_main_returns_failure_exit_code(mocker: MockerFixture, tmp_path: Path) -> None:
    """Tests CLI exits with code 1 when article ingestion fails semantically."""
    mocker.patch(
        "sys.argv",
        ["article_etl.py", "--url", "https://example.com/artigo"],
    )
    settings = mocker.Mock(raw_articles_path=tmp_path, logs_path=tmp_path / "logs")
    mocker.patch("ingestion.article_etl.load_settings", return_value=settings)
    mocker.patch("ingestion.article_etl.configure_logging")
    save_raw_article_mock = mocker.patch(
        "ingestion.article_etl.save_raw_article", return_value=None
    )
    mock_logger = mocker.Mock()
    mocker.patch("ingestion.article_etl.get_logger", return_value=mock_logger)

    from ingestion.article_etl import main

    with pytest.raises(SystemExit) as excinfo:
        main()

    assert excinfo.value.code == 1
    mock_logger.error.assert_called_with("Article ETL failed.")
    save_raw_article_mock.assert_called_once_with(
        url="https://example.com/artigo",
        raw_articles_path=tmp_path,
        filename=None,
        retry_delay_seconds=30,
        access_error_log_path=tmp_path / "logs" / "article_access_errors.jsonl",
    )


def test_fetch_and_clean_article_with_retry_retries_on_network_error(
    mocker: MockerFixture,
) -> None:
    """Tests access retry recovers from transient network errors on subsequent attempt."""
    attempts = {"count": 0}

    def fake_fetch(url: str) -> dict[str, Any] | None:
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise urllib.error.URLError("connection reset")
        return {
            "title": "Título",
            "author": "Autor",
            "date": "2026-06-07",
            "url": url,
            "content": "Conteúdo",
        }

    mocker.patch("ingestion.article_etl.fetch_and_clean_article", side_effect=fake_fetch)
    sleeper = mocker.Mock()

    result = fetch_and_clean_article_with_retry(
        "https://example.com/artigo",
        retry_delay_seconds=10,
        sleep_func=sleeper,
    )

    assert result is not None
    assert attempts["count"] == 2
    sleeper.assert_called_once_with(10)


def test_fetch_and_clean_article_with_retry_does_not_catch_value_error(
    mocker: MockerFixture,
) -> None:
    """Tests that ValueError propagates immediately without sleeping or retrying."""
    mocker.patch(
        "ingestion.article_etl.fetch_and_clean_article",
        side_effect=ValueError("Article URL cannot be empty."),
    )
    sleeper = mocker.Mock()

    with pytest.raises(ValueError, match="Article URL cannot be empty."):
        fetch_and_clean_article_with_retry(
            "",
            retry_delay_seconds=10,
            sleep_func=sleeper,
        )

    sleeper.assert_not_called()

