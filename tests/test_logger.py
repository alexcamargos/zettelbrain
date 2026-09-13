"""Unit tests for logger compatibility across loguru and stdlib fallback modes."""

from __future__ import annotations

from typing import Any

import logger as logger_module


class _FakeStdlibLogger:
    def __init__(self) -> None:
        self.records: list[tuple[str, str, tuple[Any, ...]]] = []

    def info(self, message: str, *args: Any) -> None:
        self.records.append(("info", message, args))

    def exception(self, message: str, *args: Any) -> None:
        self.records.append(("exception", message, args))


def test_log_skill_execution_uses_stdlib_placeholders_when_loguru_is_unavailable(
    monkeypatch,
) -> None:
    """Ensures stdlib fallback does not receive Loguru-style `{}` placeholders."""
    fake_logger = _FakeStdlibLogger()
    monkeypatch.setattr(logger_module, "_logger", None)
    original_get_logger = logger_module.logging.getLogger

    def mocked_get_logger(name=None):
        if name == "zettelbrain":
            return fake_logger
        return original_get_logger(name)

    monkeypatch.setattr(logger_module.logging, "getLogger", mocked_get_logger)

    @logger_module.log_skill_execution
    def sample_tool(value: int) -> int:
        return value * 2

    result = sample_tool(3)

    assert result == 6
    assert fake_logger.records[0] == (
        "info",
        "skill_start name=%s args=%s kwargs=%s",
        ("sample_tool", (3,), {}),
    )
    assert fake_logger.records[1][0] == "info"
    assert fake_logger.records[1][1] == "skill_end name=%s elapsed_ms=%.2f"


def test_configure_logging_custom_parameters(tmp_path: Any) -> None:
    """Tests configuring logger with custom level, rotation and retention.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        None

    """
    logger_instance = logger_module.configure_logging(
        tmp_path,
        level="DEBUG",
        rotation="5 MB",
        retention="7 days",
    )

    assert logger_instance is not None
    assert (tmp_path / "zettelbrain.log").exists()


def test_configure_logging_stdlib_level(tmp_path: Any, monkeypatch: Any) -> None:
    """Tests stdlib fallback respects the configured log level.

    Args:
        tmp_path: Pytest temporary directory fixture.
        monkeypatch: Pytest monkeypatch utility fixture.

    Returns:
        None

    """
    monkeypatch.setattr(logger_module, "_logger", None)
    logger_instance = logger_module.configure_logging(tmp_path, level="WARNING")

    assert logger_instance.level == logger_module.logging.WARNING
