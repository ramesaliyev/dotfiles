from __future__ import annotations

from pathlib import Path


def ask_overwrite(dest: Path) -> bool:
    """Prompt the user whether to overwrite dest. Returns True if yes."""
    try:
        answer = input(f"  ? {dest} already exists. Overwrite? [Y/n] ").strip().lower()
        return answer != "n"  # empty input (Enter) also returns True — default is yes
    except EOFError:
        return False
