from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from pathlib import Path

from src.core.events import (
    CopyDone,
    CopySkipped,
    Event,
    Info,
    ModuleEnd,
    ModuleStart,
    SubprocessRun,
    Warning,
)
from src.core.paths import load_module_config


def check_zshrc(plugin_names: list[str], zshrc: Path) -> list[str]:
    """Return plugin names missing from zshrc plugins=()."""
    if not zshrc.exists():
        return []
    lines = [ln for ln in zshrc.read_text().splitlines() if not ln.lstrip().startswith("#")]
    text = "\n".join(lines)
    match = re.search(r"plugins=\(([^)]*)\)", text, re.DOTALL)
    if not match:
        return sorted(plugin_names)
    active = set(match.group(1).split())
    return sorted(set(plugin_names) - active)


def _install_autojump(name: str, url: str) -> Iterator[Event]:
    tmp = Path("/tmp") / name
    yield SubprocessRun(["git", "clone", url, str(tmp)])
    yield SubprocessRun(["python3", "install.py"], cwd=tmp)
    yield SubprocessRun(["rm", "-rf", str(tmp)])


_CUSTOM_INSTALLERS: dict[str, Callable[[str, str], Iterator[Event]]] = {
    "autojump": _install_autojump,
}


class ZshModule:
    name = "zsh"

    def _load_config(self):
        return load_module_config(__file__)

    def bootstrap(self) -> Iterator[Event]:
        yield ModuleStart(self.name)
        cfg = yield from self._load_config()

        plugins = cfg["plugins"]
        plugin_dir = Path(cfg["plugin_dir"])
        zshrc = Path(cfg["zshrc"])

        for plugin in plugins:
            match plugin["type"]:
                case "builtin":
                    continue

                case "gitrepo" | "custom":
                    name = plugin["name"]
                    dest = plugin_dir / name

                    if dest.exists():
                        yield CopySkipped(name)
                    else:
                        match plugin["type"]:
                            case "gitrepo":
                                yield SubprocessRun(["git", "clone", plugin["url"], str(dest)])
                            case "custom":
                                yield from _CUSTOM_INSTALLERS[name](name, plugin["url"])
                        yield CopyDone(name)

        all_names = [p["name"] for p in plugins]
        missing = check_zshrc(all_names, zshrc)
        if missing:
            yield Warning(
                f"Following plugins missing from ~/.zshrc plugins=():\n"
                f"  ({' '.join(missing)})\n"
                f"  Add them and run: source ~/.zshrc"
            )

        yield ModuleEnd(
            name=self.name,
            note=cfg.get("post_bootstrap_note"),
            readme_rel=cfg.get("readme"),
        )

    def collect(self) -> Iterator[Event]:
        yield ModuleStart(self.name)
        yield Info("no files to collect — .zshrc is machine-specific")
        yield ModuleEnd(name=self.name, note=None, readme_rel=None)
