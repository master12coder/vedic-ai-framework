"""Config loader — reads config.yaml and provides typed access."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


_CONFIG: dict[str, Any] | None = None


def reset_config() -> None:
    """Clear cached config. Call between tests if needed."""
    global _CONFIG
    _CONFIG = None


def _find_config_path() -> Path:
    """Walk up from CWD looking for config.yaml, fall back to package root."""
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        candidate = parent / "config.yaml"
        if candidate.exists():
            return candidate
    # Fallback: package root
    return Path(__file__).resolve().parent.parent / "config.yaml"


def load_config(path: Path | str | None = None) -> dict[str, Any]:
    """Load and cache configuration from config.yaml."""
    global _CONFIG
    if _CONFIG is not None and path is None:
        return _CONFIG
    config_path = Path(path) if path else _find_config_path()
    if config_path.exists():
        with open(config_path) as f:
            _CONFIG = yaml.safe_load(f) or {}
    else:
        _CONFIG = {}
    return _CONFIG


def get(key: str, default: Any = None) -> Any:
    """Get a config value using dot notation (e.g. 'llm.default_backend')."""
    cfg = load_config()
    keys = key.split(".")
    value: Any = cfg
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
        else:
            return default
        if value is None:
            return default
    return value
