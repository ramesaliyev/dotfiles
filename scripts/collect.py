"""collect — copy configs from this machine into the dotfiles repo."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from scripts.common import info, warn
from scripts.modules import tmux

REPO_ROOT = Path(__file__).parent.parent


def collect_file(src: Path, dest_rel: str) -> None:
    dest = REPO_ROOT / dest_rel
    if not src.exists():
        warn(f"not found, skipping: {src}")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    info(f"collected {src} → {dest_rel}")


def collect_dir(src_dir: Path, dest_rel: str) -> None:
    if not src_dir.is_dir():
        warn(f"directory not found, skipping: {src_dir}")
        return
    dest_dir = REPO_ROOT / dest_rel
    dest_dir.mkdir(parents=True, exist_ok=True)
    for src in src_dir.glob("*.sh"):
        dest = dest_dir / src.name
        shutil.copy2(src, dest)
        info(f"collected {src} → {dest_rel}/{src.name}")


def main() -> None:
    print("→ Collecting configs into repo")

    # tmux
    print("\n[tmux]")
    for src, dest_rel in tmux.COLLECT_MAPPINGS:
        collect_file(src, dest_rel)
    collect_dir(tmux.COLLECT_THEMES_SRC, tmux.COLLECT_THEMES_DEST_REL)

    print("\n✓ Done. Commit and push to share your configs.")


if __name__ == "__main__":
    sys.exit(main())
