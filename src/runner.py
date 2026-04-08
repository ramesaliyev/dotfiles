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
from typing import TYPE_CHECKING

from src.core.events import (
    Event,
    FileConflict,
    FileCopied,
    FileSkipped,
    Info,
    InstallDone,
    InstallSkipped,
    ModuleEnd,
    ModuleStart,
    SubprocessRun,
    SyncFile,
    Warning,
)
from src.core.files import sync_file
from src.core.paths import REPO_ROOT, ppath

if TYPE_CHECKING:
    from src.core.state import State

SEP = "─" * 52


def _display(
    event: Event,
    module_counts: Counter[str],
    verbose: bool,
) -> None:
    """Print and count a display event (FileCopied, FileSkipped, etc.).

    Write events (FileCopied, InstallDone) always print — the user needs to know
    what changed. Skip events only print under --verbose since no-op is the
    expected steady-state path and would add noise to normal output.
    """
    if isinstance(event, FileCopied):
        module_counts["copied"] += 1
        print(f"  {event.action} → {ppath(event.dest)}")

    elif isinstance(event, FileSkipped):
        module_counts["skipped"] += 1
        if verbose:
            print(f"  skipped → {ppath(event.dest)}  ({event.reason})")

    elif isinstance(event, FileConflict):
        module_counts["warned"] += 1
        print(f"  ! conflict: {ppath(event.dest)}", file=sys.stderr)

    elif isinstance(event, InstallDone):
        module_counts["copied"] += 1
        print(f"  installed → {event.name}")

    elif isinstance(event, InstallSkipped):
        module_counts["skipped"] += 1
        if verbose:
            print(f"  skipped → {event.name}")

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

    for event in events:
        if isinstance(event, SyncFile):
            for sub in sync_file(event.src, event.dest, state, force=force, dry_run=dry_run):
                _display(sub, module_counts, verbose)

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
            _display(event, module_counts, verbose)

    return total
