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
    ActionRequired,
    Done,
    Event,
    FileConflict,
    FileCopied,
    GitClone,
    Info,
    InstallPackage,
    ModuleEnd,
    ModuleStart,
    Skipped,
    SubprocessRun,
    SyncFile,
    Warning,
)
from src.core.files import sync_file
from src.core.packages import install_package
from src.core.paths import ppath

if TYPE_CHECKING:
    from src.core.state import State

SEP = "─" * 52


def _display(
    event: Event,
    module_counts: Counter[str],
    verbose: bool,
) -> None:
    """Print and count a display event (FileCopied, FileSkipped, etc.).

    Write events (FileCopied, Done) always print — the user needs to know
    what changed. Skipped events only print under --verbose since no-op is the
    expected steady-state path and would add noise to normal output.
    """
    match event:
        case FileCopied(action=action, dest=dest):
            module_counts["copied"] += 1
            print(f"  {action} → {ppath(dest)}")

        case FileConflict(dest=dest):
            module_counts["warned"] += 1
            print(f"  ! conflict: {ppath(dest)}", file=sys.stderr)

        case Done(name=name):
            module_counts["copied"] += 1
            print(f"  installed → {name}")

        case Skipped(name=name, details=details):
            module_counts["skipped"] += 1
            if verbose:
                suffix = f"  ({details})" if details else ""
                print(f"  skipped → {name}{suffix}")

        case Warning(message=message):
            module_counts["warned"] += 1
            for line in message.splitlines():
                print(f"  ! {line}", file=sys.stderr)

        case Info(message=message):
            print(f"  {message}")

        case ActionRequired(message=message):
            green = "\033[32m" if sys.stdout.isatty() else ""
            reset = "\033[0m" if sys.stdout.isatty() else ""
            print(f"\n  {green}{message}{reset}")


def run(
    events: Iterator[Event],
    *,
    state: State,
    force: bool,
    dry_run: bool,
    verbose: bool = False,
) -> dict[str, int]:
    """Consume event stream, execute actions, print formatted output. Returns total counts."""

    sink = None if verbose else subprocess.DEVNULL

    total: Counter[str] = Counter()
    module_counts: Counter[str] = Counter()

    for event in events:
        match event:
            case SyncFile(src=src, dest=dest):
                for sub in sync_file(src, dest, state, force=force, dry_run=dry_run):
                    _display(sub, module_counts, verbose)

            case InstallPackage():
                for sub in install_package(event, dry_run=dry_run):
                    _display(sub, module_counts, verbose)

            case GitClone(url=url, dest=dest):
                if not dry_run:
                    subprocess.run(
                        ["git", "clone", url, str(dest)], check=True, stdout=sink, stderr=sink
                    )

            case SubprocessRun(cmd=cmd, cwd=cwd):
                if not dry_run:
                    subprocess.run(cmd, cwd=cwd, check=True, stdout=sink, stderr=sink)

            case ModuleStart(name=name):
                module_counts = Counter()
                print(f"\n{SEP}")
                print(f"[{name}]")

            case ModuleEnd(note=note):
                c = module_counts
                print(f"  {c['copied']} copied, {c['skipped']} skipped, {c['warned']} warned")

                if note:
                    print()
                    for line in note.rstrip().splitlines():
                        print(f"  {line}")

                total += module_counts
                module_counts = Counter()

            case _:
                _display(event, module_counts, verbose)

    return total
