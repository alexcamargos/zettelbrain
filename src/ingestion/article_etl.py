"""Web article ETL pipeline.

This module automates the fetching and cleaning of web articles from HTTP/HTTPS URLs
using the trafilatura library. It extracts main text as Markdown, pulls structural
metadata, and writes the output with YAML front matter into the raw articles directory.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import trafilatura

from config import load_settings
from logger import configure_logging, get_logger

DEFAULT_FETCH_RETRY_DELAY_SECONDS = 30
DEFAULT_FETCH_MAX_ATTEMPTS = 2


def fetch_and_clean_article(url: str) -> dict[str, Any] | None:
    """Download a webpage and extract its main body content and metadata.

    Args:
        url: The absolute HTTP/HTTPS URL of the web article.

    Returns:
        A dictionary containing extracted metadata and Markdown content, or
        None if the download or extraction fails. The returned dictionary has
        the following keys: 'title', 'author', 'date', 'url', 'content'.

    Raises:
        ValueError: If the provided URL is empty or invalid.

    """
    if not url.strip():
        raise ValueError("Article URL cannot be empty.")

    get_logger().info("Downloading article from URL: {}", url)
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        get_logger().error("Failed to download content from URL: {}", url)
        return None

    # Extract document metadata.
    metadata = trafilatura.extract_metadata(downloaded)

    # Extract the main article body formatted as Markdown.
    markdown_content = trafilatura.extract(
        downloaded,
        output_format="markdown",
        include_comments=False,
        include_tables=True,
    )

    if not markdown_content:
        get_logger().error("Failed to extract useful text content from URL: {}", url)
        return None

    title = metadata.title if metadata and metadata.title else "Untitled"
    author = metadata.author if metadata and metadata.author else "Unknown author"
    date = metadata.date if metadata and metadata.date else "Unknown date"

    return {
        "title": title,
        "author": author,
        "date": date,
        "url": url,
        "content": markdown_content,
    }


def fetch_and_clean_article_with_retry(
    url: str,
    *,
    max_attempts: int = DEFAULT_FETCH_MAX_ATTEMPTS,
    retry_delay_seconds: int = DEFAULT_FETCH_RETRY_DELAY_SECONDS,
    access_error_log_path: Path | None = None,
    sleep_func: Any = time.sleep,
) -> dict[str, Any] | None:
    """Fetch article content with retry on access/download failures.

    Retries are only applied to the remote access phase represented by
    ``fetch_and_clean_article`` returning ``None`` or raising an exception.

    Args:
        url: The absolute HTTP/HTTPS URL of the web article.
        max_attempts: Maximum number of attempts before giving up.
        retry_delay_seconds: Delay between attempts after an access failure.
        access_error_log_path: Optional JSONL file to persist final access failures.
        sleep_func: Injectable sleeper used mainly for testing.

    Returns:
        Extracted article payload or None after all attempts fail.

    """
    attempts = max(1, max_attempts)
    last_error: str | None = None

    for attempt in range(1, attempts + 1):
        try:
            result = fetch_and_clean_article(url)
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            result = None

        if result is not None:
            return result

        if last_error is None:
            last_error = "download_failed_or_remote_content_unavailable"

        if attempt < attempts:
            get_logger().warning(
                "Article access attempt %s/%s failed for %s. Retrying in %s seconds.",
                attempt,
                attempts,
                url,
                retry_delay_seconds,
            )
            sleep_func(retry_delay_seconds)

    get_logger().error(
        "Article access failed after %s attempts for %s. Recording for later retry.",
        attempts,
        url,
    )
    if access_error_log_path is not None:
        record_article_access_failure(
            access_error_log_path,
            url=url,
            attempts=attempts,
            error=last_error,
        )
    return None


def slugify(value: str) -> str:
    """Convert a string to a filesystem-safe slug representation.

    Args:
        value: Input string to slugify.

    Returns:
        A slugified string containing only lowercase letters, numbers, and hyphens.

    """
    # Decompose accented characters and strip accent marks.
    normalized = unicodedata.normalize("NFKD", value)
    ascii_encoded = normalized.encode("ascii", "ignore").decode("ascii")

    slug = ascii_encoded.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug[:80] or "article"


def save_raw_article(
    url: str,
    raw_articles_path: Path,
    filename: str | None = None,
    *,
    max_attempts: int = DEFAULT_FETCH_MAX_ATTEMPTS,
    retry_delay_seconds: int = DEFAULT_FETCH_RETRY_DELAY_SECONDS,
    access_error_log_path: Path | None = None,
    sleep_func: Any = time.sleep,
) -> Path | None:
    """Fetch web article content and save it as a Markdown file with YAML metadata.

    Args:
        url: The absolute HTTP/HTTPS URL of the web article.
        raw_articles_path: Target directory path for storing raw articles.
        filename: Optional output filename (e.g., 'article.md'). If omitted, a
            filename is generated automatically based on the article's title.
        max_attempts: Maximum number of fetch attempts before giving up.
        retry_delay_seconds: Delay between fetch attempts after a failure.
        access_error_log_path: Optional JSONL file for recording permanent failures.
        sleep_func: Injectable sleep function used mainly in tests.

    Returns:
        The Path to the saved Markdown file, or None if extraction fails.

    """
    data = fetch_and_clean_article_with_retry(
        url,
        max_attempts=max_attempts,
        retry_delay_seconds=retry_delay_seconds,
        access_error_log_path=access_error_log_path,
        sleep_func=sleep_func,
    )
    if not data:
        return None

    raw_articles_path.mkdir(parents=True, exist_ok=True)

    if not filename:
        slug = slugify(data["title"])
        filename = f"web-{slug}.md"
    elif not filename.endswith(".md"):
        filename = f"{filename}.md"

    output_path = raw_articles_path / filename
    retrieved_at = datetime.now(UTC).isoformat(timespec="seconds")

    # Escape quotes and backslashes for YAML front matter.
    escaped_title = data["title"].replace("\\", "\\\\").replace('"', '\\"')
    escaped_author = data["author"].replace("\\", "\\\\").replace('"', '\\"')

    lines = [
        "---",
        f'title: "{escaped_title}"',
        f'author: "{escaped_author}"',
        f'published_at: "{data["date"]}"',
        f'url: "{url}"',
        f'retrieved_at: "{retrieved_at}"',
        "source_kind: web_article",
        "---",
        "",
        f"# {data['title']}",
        "",
        "Content automatically extracted from the web. This file must be processed "
        "by the `/article` workflow before entering the ZettelBrain vault.",
        "",
        data["content"],
    ]

    content_to_write = "\n".join(lines).rstrip() + "\n"
    output_path.write_text(content_to_write, encoding="utf-8", newline="\n")

    get_logger().info("Article saved successfully at: {}", output_path)
    return output_path


def record_article_access_failure(
    access_error_log_path: Path,
    *,
    url: str,
    attempts: int,
    error: str | None,
) -> None:
    """Persist a final article access failure for later reprocessing.

    Args:
        access_error_log_path: JSONL file where failures should be appended.
        url: Failed article URL.
        attempts: Number of attempts performed.
        error: Final error summary.

    """
    access_error_log_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "failed_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "url": url,
        "attempts": attempts,
        "error": error or "unknown_access_error",
    }
    with access_error_log_path.open("a", encoding="utf-8", newline="\n") as file:
        file.write(json.dumps(payload, ensure_ascii=False) + "\n")


def main() -> None:
    """CLI entry point for the Web Article ETL pipeline.

    Parses CLI arguments, loads settings, and runs the extraction and saving processes.
    """
    parser = argparse.ArgumentParser(
        description="Ingest a web article and save it as clean Markdown."
    )
    parser.add_argument(
        "--url",
        type=str,
        required=True,
        help="The web article URL to process.",
    )
    parser.add_argument(
        "--filename",
        type=str,
        default=None,
        help="Custom filename to save (for example, my-article.md).",
    )
    parser.add_argument(
        "--retry-delay-seconds",
        type=int,
        default=DEFAULT_FETCH_RETRY_DELAY_SECONDS,
        help="Seconds to wait before retrying a failed remote access attempt.",
    )
    args = parser.parse_args()

    settings = load_settings()
    configure_logging(settings.logs_path)
    access_error_log_path = settings.logs_path / "article_access_errors.jsonl"

    try:
        saved_path = save_raw_article(
            url=args.url,
            raw_articles_path=settings.raw_articles_path,
            filename=args.filename,
            retry_delay_seconds=max(0, args.retry_delay_seconds),
            access_error_log_path=access_error_log_path,
        )
    except Exception:
        get_logger().exception("Article ETL raised an unexpected error.")
        sys.exit(1)

    if saved_path:
        get_logger().info("Article ETL completed successfully.")
        sys.exit(0)
    else:
        get_logger().error("Article ETL failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
