from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

from src.core.config import load_module_config
from src.core.events import (
    ActionRequired,
    Event,
    Info,
    InstallDone,
    InstallPackage,
    InstallSkipped,
    ModuleEnd,
    ModuleStart,
    SubprocessRun,
    Warning,
)


def _inject_plugins(missing: list[str], zshrc: Path) -> bool:
    """Add missing plugin names into the plugins=(...) block. Returns True on success.

    Skips comment lines so that an example like ``# plugins=(...)`` is not
    mistaken for the real block.
    """
    text = zshrc.read_text()
    lines = text.splitlines(keepends=True)

    # Find the byte offset where the first non-comment line containing plugins=( starts.
    offset = 0
    for line in lines:
        if not line.lstrip().startswith("#") and "plugins=(" in line:
            break
        offset += len(line)
    else:
        return False

    m = re.search(r"(plugins=\()([^)]*)(\))", text[offset:], re.DOTALL)
    if not m:
        return False

    abs_start = offset + m.start()
    abs_end = offset + m.end()
    updated = m.group(2).rstrip() + " " + " ".join(missing)
    zshrc.write_text(text[:abs_start] + m.group(1) + updated + m.group(3) + text[abs_end:])
    return True


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
                        yield InstallSkipped(name)
                    else:
                        yield SubprocessRun(["git", "clone", plugin["url"], str(dest)])
                        yield InstallDone(name)

                case "package":
                    yield InstallPackage(name=plugin["name"], managers=plugin.get("packages"))

        all_names = [p["name"] for p in plugins]

        if not zshrc.exists():
            yield Warning(
                "~/.zshrc not found — create it and add:\n  plugins=(" + " ".join(all_names) + ")"
            )
        else:
            missing = _check_zshrc(all_names, zshrc)
            if missing:
                if _inject_plugins(missing, zshrc):
                    for n in missing:
                        yield Info(f"added to .zshrc → {n}")
                    yield ActionRequired("source ~/.zshrc or open a new terminal to activate.")
                else:
                    yield Warning(
                        "No plugins=() block found in ~/.zshrc — add these manually:\n"
                        "  plugins=(" + " ".join(all_names) + ")"
                    )
            else:
                yield Info("Already up to date.")

        yield ModuleEnd(name=self.name, note=None)

    def collect(self) -> Iterator[Event]:
        yield ModuleStart(self.name)
        yield Info("no files to collect — .zshrc is machine-specific")
        yield ModuleEnd(name=self.name, note=None)
