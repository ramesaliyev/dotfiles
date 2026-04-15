from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

from src.core.config import load_module_config
from src.core.events import (
    ActionRequired,
    Event,
    Info,
    ModuleEnd,
    ModuleStart,
    SubprocessRun,
    SyncFile,
)
from src.core.files import SyncOutcome, predict_sync
from src.core.paths import REPO_ROOT
from src.core.state import load_state


def _parse_tmux_plugins(text: str) -> set[str]:
    return set(re.findall(r"set\s+-g\s+@plugin\s+'([^']+)'", text))


class TmuxModule:
    name = "tmux"

    def _load_config(self):
        return load_module_config(__file__)

    def bootstrap(self) -> Iterator[Event]:
        yield ModuleStart(self.name)
        cfg = yield from self._load_config()

        tmux_conf_entry = next(e for e in cfg["files"] if e["repo"].endswith(".tmux.conf"))
        machine_conf = Path(tmux_conf_entry["machine"]).expanduser()
        repo_conf = REPO_ROOT / tmux_conf_entry["repo"]

        state = load_state()
        outcome = predict_sync(repo_conf, machine_conf, state)
        conf_will_change = outcome in {
            SyncOutcome.WILL_COPY,
            SyncOutcome.WILL_UPDATE,
            SyncOutcome.WILL_CONFLICT,
        }

        for entry in cfg["files"]:
            repo_path = REPO_ROOT / entry["repo"]
            machine_path = Path(entry["machine"]).expanduser()
            yield SyncFile(repo_path, machine_path)

        if conf_will_change:
            yield Info("Reloading config...")
            yield SubprocessRun(["bash", "-c", "tmux source-file ~/.tmux.conf 2>/dev/null || true"])

            text_before = machine_conf.read_text() if machine_conf.exists() else ""
            text_repo = repo_conf.read_text()
            new_plugins = _parse_tmux_plugins(text_repo) - _parse_tmux_plugins(text_before)
            if new_plugins:
                yield ActionRequired(
                    "New plugins detected — in tmux: Ctrl-A R to reload, Ctrl-A I to install."
                )
        else:
            yield Info("Already up to date.")

        yield ModuleEnd(name=self.name, note=None)

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
