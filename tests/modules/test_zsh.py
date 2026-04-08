"""Tests for src/modules/zsh — config and module behavior."""

from __future__ import annotations

from pathlib import Path

import yaml

from src.core.paths import REPO_ROOT

CONFIG_PATH = REPO_ROOT / "src" / "modules" / "zsh" / "config.yaml"


def _cfg():
    with CONFIG_PATH.open() as f:
        return yaml.safe_load(f)


def _cfg_gen(cfg):
    """Generator that yields no warnings and returns cfg (for monkeypatching _load_config)."""
    if False:
        yield
    return cfg


# ---------------------------------------------------------------------------
# config.yaml structure
# ---------------------------------------------------------------------------


def test_config_has_plugins_list():
    assert isinstance(_cfg()["plugins"], list)
    assert len(_cfg()["plugins"]) >= 1


def test_each_plugin_has_name():
    for p in _cfg()["plugins"]:
        assert "name" in p
        assert isinstance(p["name"], str)


def test_plugins_with_url_are_github():
    for p in _cfg()["plugins"]:
        url = p.get("url")
        if url:
            assert url.startswith("https://github.com/")


def test_autojump_has_custom_type():
    plugins = {p["name"]: p for p in _cfg()["plugins"]}
    assert plugins["autojump"].get("type") == "custom"


def test_all_plugins_have_type():
    valid_types = {"builtin", "gitrepo", "custom"}
    for p in _cfg()["plugins"]:
        assert p.get("type") in valid_types


def test_builtin_plugins_have_no_url():
    for p in _cfg()["plugins"]:
        if p.get("type") == "builtin":
            assert "url" not in p


def test_plugin_names_are_unique():
    names = [p["name"] for p in _cfg()["plugins"]]
    assert len(names) == len(set(names))


def test_config_has_readme():
    assert isinstance(_cfg().get("readme"), str)


def test_config_has_plugin_dir():
    assert isinstance(_cfg().get("plugin_dir"), str)
    assert "$ZSH_CUSTOM" in _cfg()["plugin_dir"]


def test_config_has_zshrc():
    assert _cfg().get("zshrc") == "~/.zshrc"


# ---------------------------------------------------------------------------
# check_zshrc
# ---------------------------------------------------------------------------


import src.modules.zsh.module as zsh_mod  # noqa: E402


def test_check_zshrc_no_file(tmp_path):
    assert zsh_mod._check_zshrc(["git", "autojump"], tmp_path / ".zshrc") == []


def test_check_zshrc_all_present(tmp_path):
    names = [p["name"] for p in _cfg()["plugins"]]
    zshrc = tmp_path / ".zshrc"
    zshrc.write_text(f"plugins=({' '.join(names)})\n")
    assert zsh_mod._check_zshrc(names, zshrc) == []


def test_check_zshrc_missing_some(tmp_path):
    zshrc = tmp_path / ".zshrc"
    zshrc.write_text("plugins=(git copypath)\n")
    missing = zsh_mod._check_zshrc(["git", "copypath", "autojump", "you-should-use"], zshrc)
    assert sorted(missing) == ["autojump", "you-should-use"]


def test_check_zshrc_no_plugins_declaration(tmp_path):
    zshrc = tmp_path / ".zshrc"
    zshrc.write_text("export ZSH=$HOME/.oh-my-zsh\n")
    names = ["git", "autojump"]
    assert zsh_mod._check_zshrc(names, zshrc) == sorted(names)


def test_check_zshrc_multiline_plugins(tmp_path):
    zshrc = tmp_path / ".zshrc"
    zshrc.write_text("plugins=(\n  git\n  copypath\n)\n")
    missing = zsh_mod._check_zshrc(["git", "copypath", "autojump"], zshrc)
    assert missing == ["autojump"]


def test_check_zshrc_skips_commented_lines(tmp_path):
    zshrc = tmp_path / ".zshrc"
    zshrc.write_text("# plugins=(git autojump)\nplugins=(git)\n")
    missing = zsh_mod._check_zshrc(["git", "autojump"], zshrc)
    assert "git" not in missing
    assert "autojump" in missing


# ---------------------------------------------------------------------------
# ZshModule.bootstrap — dry run
# ---------------------------------------------------------------------------


def _test_cfg(tmp_path):
    """Return a config dict with paths pointing to tmp_path."""
    return {
        **_cfg(),
        "plugin_dir": str(tmp_path / "custom" / "plugins"),
        "zshrc": str(tmp_path / ".zshrc"),
    }


def test_bootstrap_dry_run_no_subprocess(tmp_path, monkeypatch):
    cfg_gen = lambda _: _cfg_gen(_test_cfg(tmp_path))  # noqa: E731
    monkeypatch.setattr(zsh_mod.ZshModule, "_load_config", cfg_gen)
    all_plugins = "git copypath zsh-autosuggestions zsh-syntax-highlighting you-should-use autojump"
    (tmp_path / ".zshrc").write_text(f"plugins=({all_plugins})\n")

    from src.core.events import ModuleEnd, ModuleStart
    from src.modules.zsh.module import ZshModule

    events = list(ZshModule().bootstrap())

    assert any(isinstance(e, ModuleStart) for e in events)
    assert any(isinstance(e, ModuleEnd) for e in events)


def test_bootstrap_yields_copy_done_for_new_plugins(tmp_path, monkeypatch):
    cfg_gen = lambda _: _cfg_gen(_test_cfg(tmp_path))  # noqa: E731
    monkeypatch.setattr(zsh_mod.ZshModule, "_load_config", cfg_gen)
    (tmp_path / ".zshrc").write_text("plugins=()\n")

    from src.core.events import CopyDone
    from src.modules.zsh.module import ZshModule

    events = list(ZshModule().bootstrap())

    installed = [e for e in events if isinstance(e, CopyDone)]
    assert len(installed) > 0


# ---------------------------------------------------------------------------
# ZshModule.bootstrap — all plugins already exist
# ---------------------------------------------------------------------------


def test_bootstrap_all_exist_skips_all(tmp_path, monkeypatch):
    cfg = _test_cfg(tmp_path)
    plugin_dir = Path(cfg["plugin_dir"])
    monkeypatch.setattr(zsh_mod.ZshModule, "_load_config", lambda _: _cfg_gen(cfg))
    all_plugins = "git copypath zsh-autosuggestions zsh-syntax-highlighting you-should-use autojump"
    (tmp_path / ".zshrc").write_text(f"plugins=({all_plugins})\n")

    # Pre-create all plugin dirs
    for p in _cfg()["plugins"]:
        if p.get("url"):
            (plugin_dir / p["name"]).mkdir(parents=True)

    from src.core.events import CopyDone, CopySkipped, SubprocessRun
    from src.modules.zsh.module import ZshModule

    events = list(ZshModule().bootstrap())

    assert not any(isinstance(e, SubprocessRun) for e in events)
    assert not any(isinstance(e, CopyDone) for e in events)
    assert any(isinstance(e, CopySkipped) for e in events)


# ---------------------------------------------------------------------------
# ZshModule.collect — info, no files
# ---------------------------------------------------------------------------


def test_collect_yields_info():
    from src.core.events import Info, Warning
    from src.modules.zsh.module import ZshModule

    events = list(ZshModule().collect())

    assert any(isinstance(e, Info) for e in events)
    assert not any(isinstance(e, Warning) for e in events)
