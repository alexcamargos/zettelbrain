"""Common utility functions for the ZettelBrain workspace.

Provides general helpers including string manipulation and filesystem-safe
slug generation across ingestion pipelines and vault linting.
"""

from __future__ import annotations

import re
import unicodedata

DEFAULT_SLUG_MAX_LENGTH: int = 80


def slugify(
    value: str,
    *,
    max_length: int | None = DEFAULT_SLUG_MAX_LENGTH,
    default: str = "",
) -> str:
    """Convert a string into a filesystem-safe slug representation.

    Normalizes unicode characters by stripping diacritical marks (accents),
    converts characters to lowercase, replaces non-alphanumeric sequences with
    hyphens, removes leading and trailing hyphens, and optionally truncates
    to a specified maximum length.

    Args:
        value: Input string to be normalized into a slug.
        max_length: Optional maximum character length of the resulting slug.
            Defaults to 80. If set to None or <= 0, no truncation is performed.
            Any trailing hyphens resulting from truncation are removed.
        default: Fallback string to return if the normalized slug is empty.
            Defaults to empty string ("").

    Returns:
        The normalized slug string, or the fallback default string if empty.

    Raises:
        TypeError: If value is not an instance of str.

    """
    if not isinstance(value, str):
        raise TypeError(f"Expected str, got {type(value).__name__}")

    # Decompose accented characters and strip accent marks.
    normalized = unicodedata.normalize("NFKD", value)
    ascii_encoded = normalized.encode("ascii", "ignore").decode("ascii")

    slug = ascii_encoded.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")

    if max_length is not None and max_length > 0:
        slug = slug[:max_length].rstrip("-")

    return slug or default
