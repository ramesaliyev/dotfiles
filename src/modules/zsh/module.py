from __future__ import annotations

import re
import shutil
from collections.abc import Callable, Iterator
from pathlib import Path

from src.core.config import load_module_config
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


def _check_zshrc(plugin_names: list[str], zshrc: Path) -> list[str]:
    """Return plugin names missing from zshrc plugins=().

    Strip comment lines first so a commented-out plugins=(...) block doesn't
    produce false matches. re.DOTALL lets the regex span a multi-line block.
    .split() with no args handles any mix of spaces and newlines between names.
    """
    if not zshrc.exists():
        return []
    # Drop comment lines so `# plugins=(...)` is ignored by the regex below.
    lines = [ln for ln in zshrc.read_text().splitlines() if not ln.lstrip().startswith("#")]
    text = "\n".join(lines)
    # Capture everything inside plugins=(...); re.DOTALL allows the block to
    # span multiple lines.
    match = re.search(r"plugins=\(([^)]*)\)", text, re.DOTALL)
    if not match:
        return sorted(plugin_names)
    # split() without args tokenises on any whitespace and skips empty strings.
    active = set(match.group(1).split())
    return sorted(set(plugin_names) - active)


def _install_autojump(name: str, url: str) -> Iterator[Event]:
    if shutil.which("autojump"):
        yield CopySkipped(name)
        return
    tmp = Path("/tmp") / name
    yield SubprocessRun(["git", "clone", url, str(tmp)])
    yield SubprocessRun(["python3", "install.py"], cwd=tmp)
    yield SubprocessRun(["rm", "-rf", str(tmp)])
    yield CopyDone(name)


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
                    continue  # oh-my-zsh ships builtins; nothing to install

                case "gitrepo":
                    name = plugin["name"]
                    dest = plugin_dir / name
                    if dest.exists():
                        yield CopySkipped(name)
                    else:
                        yield SubprocessRun(["git", "clone", plugin["url"], str(dest)])
                        yield CopyDone(name)

                case "custom":
                    name = plugin["name"]
                    yield from _CUSTOM_INSTALLERS[name](name, plugin["url"])

        all_names = [p["name"] for p in plugins]
        missing = _check_zshrc(all_names, zshrc)
        if missing:
            yield Warning(
                f"\n"
                f"Following plugins missing from ~/.zshrc plugins=(...):\n"
                f"  ({' '.join(missing)})\n"
                f"  Add them and run: source ~/.zshrc"
                f"\n\n"
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
