from __future__ import annotations

import os
import re
from collections.abc import Iterator
from pathlib import Path

import yaml

from src.core.events import Warning

REPO_ROOT = Path(__file__).parent.parent.parent


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
    def replacer(m: re.Match) -> str:
        var = m.group(1)
        val = os.environ.get(var)
        if val is None:
            warnings.append(f"env var ${var} is not set")
            return m.group(0)
        return val

    expanded = re.sub(r"\$([A-Z_][A-Z0-9_]*)", replacer, s)
    return str(Path(expanded).expanduser())
