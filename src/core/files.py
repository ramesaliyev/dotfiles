"""sync_file — unified collect/bootstrap engine.

Call as:
    bootstrap: sync_file(repo_path, machine_path, state, ...)
    collect:   sync_file(machine_path, repo_path, state, ...)

src  = the authoritative source for this sync operation
dest = where the file will be written

State is keyed by str(dest). The decision table is direction-agnostic:
  src missing            → Warning, skip
  dest missing           → copy (FileCopied action="copied")
  no entry, same csum    → adopt silently (FileSkipped)
  no entry, differ       → conflict: force overwrite or prompt
  nothing changed        → FileSkipped
  only src changed       → safe update (FileCopied action="updated")
  only dest changed      → local modification, leave alone (Warning)
  both changed           → conflict: force overwrite or prompt
"""

from __future__ import annotations

import shutil
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING

from src.core.checksum import checksum
from src.core.events import FileConflict, FileCopied, FileSkipped, Warning
from src.core.prompt import ask_overwrite
from src.core.time import now_iso

if TYPE_CHECKING:
    from src.core.state import State


def sync_file(
    src: Path,
    dest: Path,
    state: State,
    *,
    force: bool,
    dry_run: bool,
) -> Iterator[FileCopied | FileSkipped | FileConflict | Warning]:
    # Case: src missing - can't do anything, just warn and skip.
    if not src.exists():
        yield Warning(f"not found, skipping: {src}")
        return

    current_src_cs = checksum(src)
    dest_key = str(dest)
    entry = state["entries"].get(dest_key)

    # Case: dest missing — copy unconditionally, no conflict possible.
    if not dest.exists():
        if not dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            state["entries"][dest_key] = {
                "src_rel": str(src),
                "src_checksum": current_src_cs,
                "dest_checksum": current_src_cs,
                "synced_at": now_iso(),
            }
        yield FileCopied(src=src, dest=dest, action="copied")
        return

    current_dest_cs = checksum(dest)

    # Case: no entry, same checksum — adopt silently.
    if entry is None and current_src_cs == current_dest_cs:
        if not dry_run:
            state["entries"][dest_key] = {
                "src_rel": str(src),
                "src_checksum": current_src_cs,
                "dest_checksum": current_src_cs,
                "synced_at": now_iso(),
            }
        yield FileSkipped(dest=dest, reason="unchanged")
        return

    if entry is None:
        src_changed = True
        dest_changed = True
    else:
        src_changed = current_src_cs != entry["src_checksum"]
        dest_changed = current_dest_cs != entry["dest_checksum"]

    # Case: nothing changed — skip.
    if not src_changed and not dest_changed:
        yield FileSkipped(dest=dest, reason="unchanged")
        return

    # Case: only src changed — safe update, no conflict.
    if src_changed and not dest_changed:
        if not dry_run:
            shutil.copy2(src, dest)
            state["entries"][dest_key] = {
                "src_rel": str(src),
                "src_checksum": current_src_cs,
                "dest_checksum": current_src_cs,
                "synced_at": now_iso(),
            }
        yield FileCopied(src=src, dest=dest, action="updated")
        return

    # Case: only dest changed — local modification, leave alone.
    if not src_changed and dest_changed:
        yield Warning(f"locally modified, skipping: {dest}")
        return

    # Case: both changed — conflict, prompt or force.
    yield FileConflict(dest=dest, description="both src and dest have changed")
    do_overwrite = force or (not dry_run and ask_overwrite(dest))

    if do_overwrite:
        if not dry_run:
            shutil.copy2(src, dest)
            state["entries"][dest_key] = {
                "src_rel": str(src),
                "src_checksum": current_src_cs,
                "dest_checksum": current_src_cs,
                "synced_at": now_iso(),
            }
        yield FileCopied(src=src, dest=dest, action="overwritten")
    else:
        yield FileSkipped(dest=dest, reason="kept local")
