"""Shared utilities: state file I/O, checksum helpers, prompt helpers."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict

STATE_FILE = Path.home() / ".dotfiles" / "state.json"
STATE_VERSION = 1


class Entry(TypedDict):
    repo_rel: str
    repo_checksum: str
    dest_checksum: str
    bootstrapped_at: str


class State(TypedDict):
    version: int
    entries: dict[str, Entry]


def load_state() -> State:
    if STATE_FILE.exists():
        with STATE_FILE.open() as f:
            return json.load(f)
    return {"version": STATE_VERSION, "entries": {}}


def save_state(state: State) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with STATE_FILE.open("w") as f:
        json.dump(state, f, indent=2)
        f.write("\n")


def checksum(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def warn(msg: str) -> None:
    print(f"  ! {msg}", file=sys.stderr)


def info(msg: str) -> None:
    print(f"  {msg}")


def ask_overwrite(dest: Path) -> bool:
    """Prompt the user whether to overwrite dest. Returns True if yes."""
    try:
        answer = input(f"  ? {dest} already exists. Overwrite? [Y/n] ").strip().lower()
        return answer != "n"
    except (EOFError, KeyboardInterrupt):
        return False
