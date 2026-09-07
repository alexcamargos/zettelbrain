"""Unit tests for utility functions in the ZettelBrain workspace.

Tests the slugify function across unicode normalization, character sanitization,
length limits, fallback defaults, and parameter validation.
"""

from __future__ import annotations

from typing import Any

import pytest

from utils import DEFAULT_SLUG_MAX_LENGTH, slugify


@pytest.mark.parametrize(
    ("input_text", "expected_slug"),
    [
        ("Regressão Linear", "regressao-linear"),
        ("Algoritmo de Dijkstra!", "algoritmo-de-dijkstra"),
        ("  Termo   com Espaços  ", "termo-com-espacos"),
        ("Variável_Estatística", "variavel-estatistica"),
        ("Meu Artigo Especial! 123", "meu-artigo-especial-123"),
        ("Python -- Ingestion ETL", "python-ingestion-etl"),
        ("ÁÉÍÓÚ àèìòù âêîôû ãõ ç", "aeiou-aeiou-aeiou-ao-c"),
        ("---múltiplos---hífens---", "multiplos-hifens"),
        ("Texto & Símbolos @#$%*", "texto-simbolos"),
    ],
)
def test_slugify_basic_conversions(input_text: str, expected_slug: str) -> None:
    """Verify that slugify correctly normalizes and sanitizes various text formats.

    Args:
        input_text: The input string to slugify.
        expected_slug: The expected normalized slug string.

    Returns:
        None

    """
    assert slugify(input_text) == expected_slug


def test_slugify_empty_string_returns_default() -> None:
    """Verify that slugify returns the default fallback when result is empty.

    Returns:
        None

    """
    assert slugify("") == ""
    assert slugify("   ") == ""
    assert slugify("!@#$%^&*()") == ""
    assert slugify("", default="article") == "article"
    assert slugify("!@#$%", default="video") == "video"


def test_slugify_default_max_length() -> None:
    """Verify that the default max_length limit of 80 is enforced.

    Returns:
        None

    """
    long_input = "a" * 120
    result = slugify(long_input)
    assert len(result) == DEFAULT_SLUG_MAX_LENGTH
    assert result == "a" * 80


def test_slugify_custom_max_length_strips_trailing_hyphen() -> None:
    """Verify that custom max_length truncates and strips trailing hyphen.

    Returns:
        None

    """
    # "palavra-chave-composta" -> length is 22
    # Truncating at 8 gives "palavra-" which should be cleaned to "palavra"
    text = "palavra chave composta"
    assert slugify(text, max_length=8) == "palavra"
    assert slugify(text, max_length=13) == "palavra-chave"


def test_slugify_no_truncation_when_max_length_none_or_non_positive() -> None:
    """Verify that slugify does not truncate when max_length is None or <= 0.

    Returns:
        None

    """
    long_input = "b" * 150
    assert slugify(long_input, max_length=None) == "b" * 150
    assert slugify(long_input, max_length=0) == "b" * 150
    assert slugify(long_input, max_length=-10) == "b" * 150


@pytest.mark.parametrize(
    "invalid_input",
    [None, 123, 45.67, ["lista"], {"chave": "valor"}],
)
def test_slugify_invalid_type_raises_type_error(invalid_input: Any) -> None:
    """Verify that slugify raises TypeError when input is not a string.

    Args:
        invalid_input: Non-string input value.

    Returns:
        None

    Raises:
        TypeError: When value is not a string.

    """
    with pytest.raises(TypeError, match="Expected str, got"):
        slugify(invalid_input)
