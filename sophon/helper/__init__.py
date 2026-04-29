"""Logging utilities for Sophon library."""

import logging
from typing import Callable, Optional

from .progress import ProgressTracker, create_progress_callback

# Create logger
logger = logging.getLogger("sophon")

__all__ = ["Logger", "ProgressTracker", "create_progress_callback"]


class Logger:
    """Logger wrapper for Sophon library."""

    _log_handler: Optional[Callable[[str, str], None]] = None

    @classmethod
    def set_log_handler(cls, handler: Optional[Callable[[str, str], None]]) -> None:
        """
        Set the log handler function.

        Args:
            handler: Function that takes (level, message) as arguments.
        """
        cls._log_handler = handler

    @classmethod
    def debug(cls, message: str) -> None:
        """Log debug message."""
        logger.debug(message)
        if cls._log_handler:
            cls._log_handler("DEBUG", message)

    @classmethod
    def info(cls, message: str) -> None:
        """Log info message."""
        logger.info(message)
        if cls._log_handler:
            cls._log_handler("INFO", message)

    @classmethod
    def warning(cls, message: str) -> None:
        """Log warning message."""
        logger.warning(message)
        if cls._log_handler:
            cls._log_handler("WARNING", message)

    @classmethod
    def error(cls, message: str) -> None:
        """Log error message."""
        logger.error(message)
        if cls._log_handler:
            cls._log_handler("ERROR", message)
