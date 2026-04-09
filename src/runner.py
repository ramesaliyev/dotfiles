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
    match event:
        case FileCopied(action=action, dest=dest):
            module_counts["copied"] += 1
            print(f"  {action} → {ppath(dest)}")

        case FileSkipped(dest=dest, reason=reason):
            module_counts["skipped"] += 1
            if verbose:
                print(f"  skipped → {ppath(dest)}  ({reason})")

        case FileConflict(dest=dest):
            module_counts["warned"] += 1
            print(f"  ! conflict: {ppath(dest)}", file=sys.stderr)

        case InstallDone(name=name):
            module_counts["copied"] += 1
            print(f"  installed → {name}")

        case InstallSkipped(name=name):
            module_counts["skipped"] += 1
            if verbose:
                print(f"  skipped → {name}")

        case Warning(message=message):
            module_counts["warned"] += 1
            for line in message.splitlines():
                print(f"  ! {line}", file=sys.stderr)

        case Info(message=message):
            print(f"  {message}")


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
        match event:
            case SyncFile(src=src, dest=dest):
                for sub in sync_file(src, dest, state, force=force, dry_run=dry_run):
                    _display(sub, module_counts, verbose)

            case SubprocessRun(cmd=cmd, cwd=cwd):
                if not dry_run:
                    sink = None if verbose else subprocess.DEVNULL
                    subprocess.run(cmd, cwd=cwd, check=True, stdout=sink, stderr=sink)

            case ModuleStart(name=name):
                module_counts = Counter()
                print(f"\n{SEP}")
                print(f"[{name}]")

            case ModuleEnd(note=note, readme_rel=readme_rel):
                c = module_counts
                print(f"  {c['copied']} copied, {c['skipped']} skipped, {c['warned']} warned")

                if note:
                    print()
                    for line in note.rstrip().splitlines():
                        print(f"  {line}")

                if readme_rel:
                    readme = REPO_ROOT / readme_rel
                    if readme.exists():
                        print(f"  See: {readme_rel}")

                total += module_counts
                module_counts = Counter()

            case _:
                _display(event, module_counts, verbose)

    return total
