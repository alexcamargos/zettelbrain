"""Logging configuration module for the LLM ZettelBrain project.

Sets up structured logging using either `loguru` (if installed) or fallback
to the standard library's `logging` module. Provides decorators to instrument
performance tracking and error capture for MCP tool executions.
"""

from __future__ import annotations

import functools
import logging
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

try:
    from loguru import logger as _logger
except ImportError:  # pragma: no cover - exercised only without optional dependency
    _logger = None

F = TypeVar("F", bound=Callable[..., Any])


def configure_logging(logs_path: Path) -> Any:
    """Configure structured logs with loguru when available, otherwise stdlib logging.

    Args:
        logs_path: Path to the directory where log files should be created.

    Returns:
        Any: A loguru logger instance or a standard logging Logger instance.

    """
    logs_path.mkdir(parents=True, exist_ok=True)
    log_file = logs_path / "zettelbrain.log"

    if _logger is not None:
        _logger.remove()
        _logger.add(
            sink=sys.stderr,
            colorize=True,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}",
        )
        _logger.add(
            log_file,
            rotation="10 MB",
            retention="14 days",
            encoding="utf-8",
            enqueue=True,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        )
        return _logger

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    return logging.getLogger("zettelbrain")


def get_logger() -> Any:
    """Retrieve the configured logger instance.

    Returns:
        Any: The loguru logger instance if available, or the standard logging fallback.

    """
    if _logger is not None:
        return _logger
    return logging.getLogger("zettelbrain")


def log_skill_execution(func: F) -> F:
    """Log function name, elapsed time and failures for MCP tool handlers.

    Args:
        func: The callable MCP tool handler to decorate.

    Returns:
        F: The decorated callable wrapper.

    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        """Measure elapsed time and log errors for decorated MCP tool handlers.

        Args:
            *args: Variable positional arguments for the decorated function.
            **kwargs: Variable keyword arguments for the decorated function.

        Returns:
            Any: The result of the decorated function.

        Raises:
            Exception: Re-raises any exception caught from the decorated function.

        """
        logger = get_logger()
        started = time.perf_counter()
        tool_name = func.__name__
        if _logger is not None:
            logger.info("skill_start name={} args={} kwargs={}", tool_name, args, kwargs)
        else:
            logger.info("skill_start name=%s args=%s kwargs=%s", tool_name, args, kwargs)
        try:
            result = func(*args, **kwargs)
        except Exception:
            elapsed_ms = (time.perf_counter() - started) * 1000
            if _logger is not None:
                logger.exception("skill_error name={} elapsed_ms={:.2f}", tool_name, elapsed_ms)
            else:
                logger.exception("skill_error name=%s elapsed_ms=%.2f", tool_name, elapsed_ms)
            raise
        elapsed_ms = (time.perf_counter() - started) * 1000
        if _logger is not None:
            logger.info("skill_end name={} elapsed_ms={:.2f}", tool_name, elapsed_ms)
        else:
            logger.info("skill_end name=%s elapsed_ms=%.2f", tool_name, elapsed_ms)
        return result

    return wrapper  # type: ignore[return-value]
