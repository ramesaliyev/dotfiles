"""install_package — centralized OS package installation handler.

Mirrors the sync_file pattern: the caller yields InstallPackage; the runner
expands it by calling install_package(), which yields display-only events.

_KNOWN_MANAGERS maps a logical key to the full install command.
cmd[0] doubles as the binary used to detect whether the PM is available.
"""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Iterator

from src.core.events import Done, InstallPackage, Skipped, Warning

# key → full install command; cmd[0] is also the binary to detect
_KNOWN_MANAGERS: dict[str, list[str]] = {
    "apt": ["apt-get", "install", "-y"],
    "dnf": ["dnf", "install", "-y"],
    "brew": ["brew", "install"],
}


def install_package(
    event: InstallPackage,
    *,
    dry_run: bool,
    sink: int | None = subprocess.DEVNULL,
) -> Iterator[Done | Skipped | Warning]:
    if shutil.which(event.name):
        yield Skipped(event.name)
        return

    managers = (
        event.managers if event.managers is not None else dict.fromkeys(_KNOWN_MANAGERS, event.name)
    )

    for key, cmd in _KNOWN_MANAGERS.items():
        if shutil.which(cmd[0]) and key in managers:
            if not dry_run:
                subprocess.run([*cmd, managers[key]], check=True, stdout=sink, stderr=sink)
            yield Done(event.name)
            return

    yield Warning(f"No supported package manager found for {event.name}.")
