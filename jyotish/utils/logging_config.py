"""Structured logging configuration."""

from __future__ import annotations

import logging
import sys
from typing import Any


def setup_logging(level: str = "INFO", json_format: bool = False) -> None:
    """Configure structured logging for the framework.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        json_format: If True, output logs as JSON lines
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    if json_format:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger("jyotish")
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)


class JsonFormatter(logging.Formatter):
    """Format log records as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as a JSON string."""
        import json
        log_data: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)
        if record.exc_info and record.exc_info[1]:
            log_data["exception"] = str(record.exc_info[1])
        return json.dumps(log_data, default=str)


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a module.

    Args:
        name: Module name, typically __name__
    """
    return logging.getLogger(name)
