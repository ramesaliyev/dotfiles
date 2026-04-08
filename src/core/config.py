from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import yaml

from src.core.events import Warning
from src.core.shell import expand_env_vars


def load_module_config(module_file: str | Path) -> Iterator[Warning]:
    """Load config.yaml next to module_file, expand env vars and ~.

    Yields Warning events for unresolvable env vars.
    Returns the expanded config dict (captured via ``cfg = yield from load_module_config(...)``).
    """
    config_path = Path(module_file).parent / "config.yaml"
    with config_path.open() as f:
        raw = yaml.safe_load(f)
    warnings: list[str] = []
    expanded = _expand_recursive(raw, warnings)
    for w in warnings:
        yield Warning(w)
    return expanded


def _expand_recursive(obj: object, warnings: list[str]) -> object:
    if isinstance(obj, str):
        return _expand_str(obj, warnings)
    if isinstance(obj, dict):
        return {k: _expand_recursive(v, warnings) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_expand_recursive(item, warnings) for item in obj]
    return obj


def _expand_str(s: str, warnings: list[str]) -> str:
    expanded, new_warnings = expand_env_vars(s)
    warnings.extend(new_warnings)
    return expanded
