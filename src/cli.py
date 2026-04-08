"""cli — bootstrap and collect entry points."""

from __future__ import annotations

import argparse
import sys
from itertools import chain

from src.core.state import load_state, save_state
from src.modules.tmux.module import TmuxModule
from src.modules.zsh.module import ZshModule
from src.runner import run

_MESSAGES = {
    "bootstrap": {
        "header": "→ Bootstrapping from repo",
        "dry_header": "→ Bootstrapping (dry run — no changes will be made)",
        "description": "Bootstrap this machine from dotfiles repo.",
    },
    "collect": {
        "header": "→ Collecting configs into repo",
        "dry_header": "→ Collecting configs (dry run — no changes will be made)",
        "description": "Collect configs from this machine into the repo.",
    },
}


def _parse_args(command: str) -> argparse.Namespace:
    msg = _MESSAGES[command]
    parser = argparse.ArgumentParser(description=msg["description"])
    parser.add_argument("--force", action="store_true", help="overwrite conflicts, no prompts")
    parser.add_argument("--dry-run", action="store_true", help="preview without making changes")
    parser.add_argument("--verbose", action="store_true", help="show skipped files and subcommands")
    return parser.parse_args()


def _main(command: str) -> None:
    args = _parse_args(command)
    msg = _MESSAGES[command]
    print(msg["dry_header"] if args.dry_run else msg["header"])

    state = load_state()
    modules = [TmuxModule(), ZshModule()]
    raw = chain.from_iterable(getattr(m, command)() for m in modules)
    counts = run(raw, state=state, force=args.force, dry_run=args.dry_run, verbose=args.verbose)

    if not args.dry_run:
        save_state(state)

    print(f"\n{'─' * 52}")
    c = counts
    print(f"✓ Done — {c['copied']} copied, {c['skipped']} skipped, {c['warned']} warned")
    if counts["warned"] and not args.force:
        print("  Run with --force to overwrite conflicts automatically.")


def _entry(command: str) -> None:
    try:
        _main(command)
    except KeyboardInterrupt:
        print("\nAborted.", file=sys.stderr)
        sys.exit(1)


def bootstrap() -> None:
    _entry("bootstrap")


def collect() -> None:
    _entry("collect")
