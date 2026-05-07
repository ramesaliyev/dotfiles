"""sync_file — unified collect/bootstrap engine.

Call as:
    bootstrap: sync_file(repo_path, machine_path, state, ...)
    collect:   sync_file(machine_path, repo_path, state, ...)

src  = the authoritative source for this sync operation
dest = where the file will be written

State is keyed by str(dest). The decision table is direction-agnostic:
  src missing            → Warning, skip
  dest missing           → copy (FileCopied action="copied")
  no entry, same csum    → adopt silently (Skipped)
  no entry, differ       → conflict: force overwrite or prompt
  nothing changed        → Skipped
  only src changed       → safe update (FileCopied action="updated")
  only dest changed      → local modification, leave alone (Warning)
  both changed           → conflict: force overwrite or prompt
"""

from __future__ import annotations

import shutil
from collections.abc import Iterator
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from src.core.checksum import checksum
from src.core.events import FileConflict, FileCopied, Skipped, Warning
from src.core.paths import ppath
from src.core.prompt import ask_overwrite
from src.core.time import now_iso

if TYPE_CHECKING:
    from src.core.state import State


class SyncOutcome(Enum):
    SRC_MISSING = "src_missing"  # src doesn't exist → Warning, skip
    WILL_COPY = "will_copy"  # dest missing → will copy unconditionally
    UNCHANGED = "unchanged"  # nothing to do (Skipped)
    WILL_UPDATE = "will_update"  # only src changed → safe update
    LOCAL_MODIFIED = "local_modified"  # only dest changed → leave alone (Warning)
    WILL_CONFLICT = "will_conflict"  # both changed → needs resolution


def predict_sync(src: Path, dest: Path, state: State) -> SyncOutcome:
    """Predict the outcome of syncing src → dest without performing any changes."""
    if not src.exists():
        return SyncOutcome.SRC_MISSING
    if not dest.exists():
        return SyncOutcome.WILL_COPY

    current_src_cs = checksum(src)
    current_dest_cs = checksum(dest)
    entry = state["entries"].get(str(dest))

    # If src and dest already match byte-for-byte, there's nothing to copy
    # regardless of state history (e.g. both sides were edited to the same value).
    if current_src_cs == current_dest_cs:
        return SyncOutcome.UNCHANGED

    if entry is None:
        src_changed = True
        dest_changed = True
    else:
        src_changed = current_src_cs != entry["src_checksum"]
        dest_changed = current_dest_cs != entry["dest_checksum"]

    if not src_changed and not dest_changed:
        return SyncOutcome.UNCHANGED
    if src_changed and not dest_changed:
        return SyncOutcome.WILL_UPDATE
    if not src_changed and dest_changed:
        return SyncOutcome.LOCAL_MODIFIED
    return SyncOutcome.WILL_CONFLICT


def sync_file(
    src: Path,
    dest: Path,
    state: State,
    *,
    force: bool,
    dry_run: bool,
) -> Iterator[FileCopied | FileConflict | Skipped | Warning]:
    outcome = predict_sync(src, dest, state)
    dest_key = str(dest)
    entries = state["entries"]

    def update_state() -> None:
        if not dry_run:
            csum = checksum(src)
            entries[dest_key] = {
                "src_rel": str(src),
                "src_checksum": csum,
                "dest_checksum": csum,
                "synced_at": now_iso(),
            }

    def copy_and_update_state() -> None:
        if not dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            update_state()

    match outcome:
        case SyncOutcome.SRC_MISSING:
            yield Warning(f"not found, skipping: {src}")

        case SyncOutcome.WILL_COPY:
            copy_and_update_state()
            yield FileCopied(src=src, dest=dest, action="copied")

        case SyncOutcome.UNCHANGED:
            update_state()
            yield Skipped(name=ppath(dest), details="unchanged")

        case SyncOutcome.WILL_UPDATE:
            copy_and_update_state()
            yield FileCopied(src=src, dest=dest, action="updated")

        case SyncOutcome.LOCAL_MODIFIED:
            yield Warning(f"locally modified, skipping: {dest}")

        case SyncOutcome.WILL_CONFLICT:
            yield FileConflict(dest=dest, description="both src and dest have changed")
            do_overwrite = force or (not dry_run and ask_overwrite(dest))

            if do_overwrite:
                copy_and_update_state()
                yield FileCopied(src=src, dest=dest, action="overwritten")
            else:
                yield Skipped(name=ppath(dest), details="kept local")
