from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict

STATE_FILE = Path.home() / ".dotfiles" / "state.json"
STATE_VERSION = 1


class Entry(TypedDict):
    src_rel: str
    src_checksum: str
    dest_checksum: str
    synced_at: str


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
