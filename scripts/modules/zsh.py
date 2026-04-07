"""zsh module — plugin installation and .zshrc health check."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from scripts.common import info

HOME = Path.home()

README_REL = "dotfiles/zsh/README.md"

POST_BOOTSTRAP_NOTE = (
    "No .zshrc committed — it's machine-specific.\n"
    "Make sure your ~/.zshrc includes full list of plugins."
)

_ZSH_CUSTOM = Path(os.environ.get("ZSH_CUSTOM", str(HOME / ".oh-my-zsh/custom")))

PLUGINS: list[tuple[str, str, Path]] = [
    (
        "zsh-autosuggestions",
        "https://github.com/zsh-users/zsh-autosuggestions",
        _ZSH_CUSTOM / "plugins/zsh-autosuggestions",
    ),
    (
        "zsh-syntax-highlighting",
        "https://github.com/zsh-users/zsh-syntax-highlighting",
        _ZSH_CUSTOM / "plugins/zsh-syntax-highlighting",
    ),
    (
        "you-should-use",
        "https://github.com/MichaelAquilina/zsh-you-should-use.git",
        _ZSH_CUSTOM / "plugins/you-should-use",
    ),
]

AUTOJUMP_DEST = HOME / ".autojump"
AUTOJUMP_URL = "https://github.com/wting/autojump.git"

EXPECTED_PLUGINS = {
    "git",
    "copypath",
    "autojump",
    "you-should-use",
    "zsh-autosuggestions",
    "zsh-syntax-highlighting",
}

BOOTSTRAP_MAPPINGS: list = []  # No config files to copy — .zshrc is machine-specific


def run_bootstrap(dry_run: bool = False, verbose: bool = False) -> dict:
    """Install missing oh-my-zsh plugins. Returns {"installed": N, "skipped": N}."""
    counts = {"installed": 0, "skipped": 0}
    sink = None if verbose else subprocess.DEVNULL

    for name, url, dest in PLUGINS:
        if dest.exists():
            counts["skipped"] += 1
            if verbose:
                info(f"[skip] {name}")
        elif dry_run:
            info(f"[dry-run] would install {name}")
            counts["installed"] += 1
        else:
            info(f"[install] {name}")
            subprocess.run(["git", "clone", url, str(dest)], check=True, stdout=sink, stderr=sink)
            counts["installed"] += 1

    # autojump uses its own install.py rather than a simple clone
    if AUTOJUMP_DEST.exists():
        counts["skipped"] += 1
        if verbose:
            info("[skip] autojump")
    elif dry_run:
        info("[dry-run] would install autojump")
        counts["installed"] += 1
    else:
        info("[install] autojump")
        tmp = Path("/tmp/autojump")
        subprocess.run(
            ["git", "clone", AUTOJUMP_URL, str(tmp)],
            check=True,
            stdout=sink,
            stderr=sink,
        )
        subprocess.run(["python3", "install.py"], cwd=tmp, check=True, stdout=sink, stderr=sink)
        counts["installed"] += 1

    return counts


def check_zshrc() -> list[str]:
    """Read ~/.zshrc and return expected plugin names missing from plugins=()."""
    zshrc = HOME / ".zshrc"
    if not zshrc.exists():
        return []
    lines = [ln for ln in zshrc.read_text().splitlines() if not ln.lstrip().startswith("#")]
    text = "\n".join(lines)
    match = re.search(r"plugins=\(([^)]*)\)", text, re.DOTALL)
    if not match:
        return sorted(EXPECTED_PLUGINS)
    active = set(match.group(1).split())
    return sorted(EXPECTED_PLUGINS - active)
