"""runner — single dispatch point for the event pipeline.

Consumes the raw event stream from modules, handles all event types:
  SyncFile      → expands inline via sync_file(), prints + counts results
  SubprocessRun → executes subprocess (unless dry_run)
  display events → prints formatted output, accumulates counts
"""

from __future__ import annotations

import subprocess
import sys
from collections import Counter
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING

from src.core.events import (
    CopyDone,
    CopySkipped,
    Event,
    FileConflict,
    FileCopied,
    FileSkipped,
    Info,
    ModuleEnd,
    ModuleStart,
    SubprocessRun,
    SyncFile,
    Warning,
)
from src.core.files import sync_file
from src.core.paths import HOME, REPO_ROOT

if TYPE_CHECKING:
    from src.core.state import State

SEP = "─" * 52


def _short(path: Path) -> str:
    """Replace home dir with ~ for display."""
    try:
        return "~/" + str(path.relative_to(HOME))
    except ValueError:
        try:
            return str(path.relative_to(REPO_ROOT))
        except ValueError:
            return str(path)


def _display(
    event: Event,
    module_counts: Counter[str],
    prefix: str,
    verbose: bool,
) -> None:
    """Print and count a display event (FileCopied, FileSkipped, etc.).

    Write events (FileCopied, CopyDone) always print — the user needs to know
    what changed. Skip events only print under --verbose since no-op is the
    expected steady-state path and would add noise to normal output.
    """
    if isinstance(event, FileCopied):
        module_counts["copied"] += 1
        print(f"  {prefix}{event.action} → {_short(event.dest)}")

    elif isinstance(event, FileSkipped):
        module_counts["skipped"] += 1
        if verbose:
            print(f"  skipped → {_short(event.dest)}  ({event.reason})")

    elif isinstance(event, FileConflict):
        module_counts["warned"] += 1
        print(f"  ! conflict: {_short(event.dest)}", file=sys.stderr)

    elif isinstance(event, CopyDone):
        module_counts["copied"] += 1
        print(f"  {prefix}install {event.name}")

    elif isinstance(event, CopySkipped):
        module_counts["skipped"] += 1
        if verbose:
            print(f"  skip    {event.name}")

    elif isinstance(event, Warning):
        module_counts["warned"] += 1
        for line in event.message.splitlines():
            print(f"  ! {line}", file=sys.stderr)

    elif isinstance(event, Info):
        print(f"  {event.message}")


def run(
    events: Iterator[Event],
    *,
    state: State,
    force: bool,
    dry_run: bool,
    verbose: bool = False,
) -> dict[str, int]:
    """Consume event stream, execute actions, print formatted output. Returns total counts."""

    total: Counter[str] = Counter()
    module_counts: Counter[str] = Counter()
    prefix = "[dry-run] " if dry_run else ""

    for event in events:
        if isinstance(event, SyncFile):
            for sub in sync_file(event.src, event.dest, state, force=force, dry_run=dry_run):
                _display(sub, module_counts, prefix, verbose)

        elif isinstance(event, SubprocessRun):
            if not dry_run:
                sink = None if verbose else subprocess.DEVNULL
                subprocess.run(event.cmd, cwd=event.cwd, check=True, stdout=sink, stderr=sink)

        elif isinstance(event, ModuleStart):
            module_counts = Counter()
            print(f"\n{SEP}")
            print(f"[{event.name}]")

        elif isinstance(event, ModuleEnd):
            c = module_counts
            print(f"  {c['copied']} copied, {c['skipped']} skipped, {c['warned']} warned")

            if event.note:
                print()
                for line in event.note.rstrip().splitlines():
                    print(f"  {line}")

            if event.readme_rel:
                readme = REPO_ROOT / event.readme_rel
                if readme.exists():
                    print(f"  See: {event.readme_rel}")

            total += module_counts
            module_counts = Counter()

        else:
            _display(event, module_counts, prefix, verbose)

    return total
