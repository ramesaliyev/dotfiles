from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from src.core.config import load_module_config
from src.core.events import (
    Event,
    ModuleEnd,
    ModuleStart,
    SyncFile,
)
from src.core.paths import REPO_ROOT


class TmuxModule:
    name = "tmux"

    def _load_config(self):
        return load_module_config(__file__)

    def bootstrap(self) -> Iterator[Event]:
        yield ModuleStart(self.name)
        cfg = yield from self._load_config()

        for entry in cfg["files"]:
            repo_path = REPO_ROOT / entry["repo"]
            machine_path = Path(entry["machine"]).expanduser()
            yield SyncFile(repo_path, machine_path)

        yield ModuleEnd(
            name=self.name,
            note=cfg.get("post_bootstrap_note"),
        )

    def collect(self) -> Iterator[Event]:
        yield ModuleStart(self.name)
        cfg = yield from self._load_config()

        for entry in cfg["files"]:
            machine_path = Path(entry["machine"]).expanduser()
            repo_path = REPO_ROOT / entry["repo"]
            yield SyncFile(machine_path, repo_path)

        yield ModuleEnd(
            name=self.name,
            note=None,
        )
