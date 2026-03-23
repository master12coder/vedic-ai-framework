"""Utilities for full_analysis.py — safe_compute wrapper and constants."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any


logger = logging.getLogger(__name__)


def safe_compute(fn: Callable, *args: Any, **kwargs: Any) -> Any:
    """Call a computation function. On crash, log and return empty list."""
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        logger.warning("Computation %s failed: %s", fn.__name__, e)
        return []
