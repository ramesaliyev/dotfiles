"""Tests for src/modules/zsh — config and module behavior."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import yaml

CONFIG_PATH = Path(__file__).parent.parent.parent / "src" / "modules" / "zsh" / "config.yaml"


def _cfg():
    with CONFIG_PATH.open() as f:
        return yaml.safe_load(f)


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


def test_autojump_has_custom_install():
    plugins = {p["name"]: p for p in _cfg()["plugins"]}
    assert plugins["autojump"].get("install") == "custom"


def test_plugins_without_url_have_no_install_key():
    for p in _cfg()["plugins"]:
        if not p.get("url"):
            assert "install" not in p


def test_plugin_names_are_unique():
    names = [p["name"] for p in _cfg()["plugins"]]
    assert len(names) == len(set(names))


def test_config_has_readme():
    assert isinstance(_cfg().get("readme"), str)


# ---------------------------------------------------------------------------
# _check_zshrc
# ---------------------------------------------------------------------------


import src.modules.zsh.module as zsh_mod  # noqa: E402


def test_check_zshrc_no_file(tmp_path, monkeypatch):
    monkeypatch.setattr(zsh_mod, "HOME", tmp_path)
    assert zsh_mod.check_zshrc(["git", "autojump"]) == []


def test_check_zshrc_all_present(tmp_path, monkeypatch):
    monkeypatch.setattr(zsh_mod, "HOME", tmp_path)
    names = [p["name"] for p in _cfg()["plugins"]]
    (tmp_path / ".zshrc").write_text(f"plugins=({' '.join(names)})\n")
    assert zsh_mod.check_zshrc(names) == []


def test_check_zshrc_missing_some(tmp_path, monkeypatch):
    monkeypatch.setattr(zsh_mod, "HOME", tmp_path)
    (tmp_path / ".zshrc").write_text("plugins=(git copypath)\n")
    missing = zsh_mod.check_zshrc(["git", "copypath", "autojump", "you-should-use"])
    assert sorted(missing) == ["autojump", "you-should-use"]


def test_check_zshrc_no_plugins_declaration(tmp_path, monkeypatch):
    monkeypatch.setattr(zsh_mod, "HOME", tmp_path)
    (tmp_path / ".zshrc").write_text("export ZSH=$HOME/.oh-my-zsh\n")
    names = ["git", "autojump"]
    assert zsh_mod.check_zshrc(names) == sorted(names)


def test_check_zshrc_skips_commented_lines(tmp_path, monkeypatch):
    monkeypatch.setattr(zsh_mod, "HOME", tmp_path)
    (tmp_path / ".zshrc").write_text("# plugins=(git autojump)\nplugins=(git)\n")
    missing = zsh_mod.check_zshrc(["git", "autojump"])
    assert "git" not in missing
    assert "autojump" in missing


# ---------------------------------------------------------------------------
# ZshModule.bootstrap — dry run
# ---------------------------------------------------------------------------


def test_bootstrap_dry_run_no_subprocess(tmp_path, monkeypatch):
    from argparse import Namespace

    monkeypatch.setattr(zsh_mod, "HOME", tmp_path)
    monkeypatch.setattr(zsh_mod, "_ZSH_CUSTOM", tmp_path / "custom")
    all_plugins = "git copypath zsh-autosuggestions zsh-syntax-highlighting you-should-use autojump"
    (tmp_path / ".zshrc").write_text(f"plugins=({all_plugins})\n")

    from src.modules.zsh.module import ZshModule
    from src.ui.events import PluginInstalled

    args = Namespace(force=False, dry_run=True, verbose=False)
    with patch("src.modules.zsh.module.subprocess.run") as mock_run:
        events = list(ZshModule().bootstrap(args, {}))

    mock_run.assert_not_called()
    installed = [e for e in events if isinstance(e, PluginInstalled)]
    assert all(e.dry_run for e in installed)


# ---------------------------------------------------------------------------
# ZshModule.bootstrap — all plugins already exist
# ---------------------------------------------------------------------------


def test_bootstrap_all_exist_skips_all(tmp_path, monkeypatch):
    from argparse import Namespace

    monkeypatch.setattr(zsh_mod, "HOME", tmp_path)
    custom = tmp_path / "custom"
    monkeypatch.setattr(zsh_mod, "_ZSH_CUSTOM", custom)
    all_plugins = "git copypath zsh-autosuggestions zsh-syntax-highlighting you-should-use autojump"
    (tmp_path / ".zshrc").write_text(f"plugins=({all_plugins})\n")

    # Pre-create all plugin dirs
    for p in _cfg()["plugins"]:
        if p.get("url"):
            (custom / "plugins" / p["name"]).mkdir(parents=True)

    from src.modules.zsh.module import ZshModule
    from src.ui.events import PluginInstalled, PluginSkipped

    args = Namespace(force=False, dry_run=False, verbose=False)
    with patch("src.modules.zsh.module.subprocess.run") as mock_run:
        events = list(ZshModule().bootstrap(args, {}))

    mock_run.assert_not_called()
    assert not any(isinstance(e, PluginInstalled) for e in events)
    assert any(isinstance(e, PluginSkipped) for e in events)


# ---------------------------------------------------------------------------
# ZshModule.collect — always warns, no files
# ---------------------------------------------------------------------------


def test_collect_yields_warning(tmp_path, monkeypatch):
    from argparse import Namespace

    monkeypatch.setattr(zsh_mod, "HOME", tmp_path)

    from src.modules.zsh.module import ZshModule
    from src.ui.events import Warning

    args = Namespace(force=False, dry_run=False, verbose=False)
    events = list(ZshModule().collect(args, {}))

    assert any(isinstance(e, Warning) for e in events)
