"""
Centralized logging utilities for Direktor.

Library modules should call :func:`get_logger` and emit log records. The CLI
and other entry points are responsible for configuring the root handler so
that importing the package does not produce side effects.
"""

from __future__ import annotations

import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the ``direktor`` namespace."""
    return logging.getLogger(f"direktor.{name}")


def configure_logging(level: str = "INFO", *, log_file: str | None = None) -> None:
    """
    Configure the root ``direktor`` logger.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to a log file. If provided, a file handler is
            added in addition to the console handler.
    """
    logger = logging.getLogger("direktor")
    logger.setLevel(level.upper())

    # Avoid adding duplicate handlers if configure_logging is called twice.
    if logger.handlers:
        return

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
