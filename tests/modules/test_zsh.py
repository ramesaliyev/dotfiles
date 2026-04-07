"""Tests for scripts/modules/zsh.py — plugin installation and .zshrc check."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import call, patch

import pytest

import scripts.modules.zsh as zsh_module


# ---------------------------------------------------------------------------
# PLUGINS constant
# ---------------------------------------------------------------------------

def test_plugins_list_length():
    assert len(zsh_module.PLUGINS) == 3


def test_plugins_structure():
    for entry in zsh_module.PLUGINS:
        name, url, dest = entry
        assert isinstance(name, str)
        assert isinstance(url, str)
        assert isinstance(dest, Path)


def test_plugins_urls_are_github():
    for _, url, _ in zsh_module.PLUGINS:
        assert url.startswith("https://github.com/")


# ---------------------------------------------------------------------------
# EXPECTED_PLUGINS constant
# ---------------------------------------------------------------------------

def test_expected_plugins_is_set_of_strings():
    assert isinstance(zsh_module.EXPECTED_PLUGINS, set)
    for p in zsh_module.EXPECTED_PLUGINS:
        assert isinstance(p, str)


# ---------------------------------------------------------------------------
# run_bootstrap — dry_run
# ---------------------------------------------------------------------------

def test_run_bootstrap_dry_run_no_clones(tmp_path, monkeypatch):
    # Point all plugin dest dirs to non-existent paths under tmp_path
    fake_plugins = [
        (name, url, tmp_path / "plugins" / name)
        for name, url, _ in zsh_module.PLUGINS
    ]
    monkeypatch.setattr(zsh_module, "PLUGINS", fake_plugins)
    monkeypatch.setattr(zsh_module, "AUTOJUMP_DEST", tmp_path / "autojump")

    with patch("scripts.modules.zsh.subprocess.run") as mock_run:
        counts = zsh_module.run_bootstrap(dry_run=True)

    mock_run.assert_not_called()
    # 3 plugins + autojump = 4 "installed" in dry-run
    assert counts == {"installed": 4, "skipped": 0}


# ---------------------------------------------------------------------------
# run_bootstrap — all plugins already exist
# ---------------------------------------------------------------------------

def test_run_bootstrap_all_exist_skip_all(tmp_path, monkeypatch):
    fake_plugins = []
    for name, url, _ in zsh_module.PLUGINS:
        dest = tmp_path / "plugins" / name
        dest.mkdir(parents=True)
        fake_plugins.append((name, url, dest))
    monkeypatch.setattr(zsh_module, "PLUGINS", fake_plugins)

    autojump_dest = tmp_path / "autojump"
    autojump_dest.mkdir()
    monkeypatch.setattr(zsh_module, "AUTOJUMP_DEST", autojump_dest)

    with patch("scripts.modules.zsh.subprocess.run") as mock_run:
        counts = zsh_module.run_bootstrap(dry_run=False)

    mock_run.assert_not_called()
    assert counts == {"installed": 0, "skipped": 4}


# ---------------------------------------------------------------------------
# run_bootstrap — none exist, real install
# ---------------------------------------------------------------------------

def test_run_bootstrap_none_exist_calls_clone(tmp_path, monkeypatch):
    fake_plugins = [
        (name, url, tmp_path / "plugins" / name)
        for name, url, _ in zsh_module.PLUGINS
    ]
    monkeypatch.setattr(zsh_module, "PLUGINS", fake_plugins)
    monkeypatch.setattr(zsh_module, "AUTOJUMP_DEST", tmp_path / "autojump")
    monkeypatch.setattr(zsh_module, "AUTOJUMP_URL", "https://github.com/wting/autojump.git")

    with patch("scripts.modules.zsh.subprocess.run") as mock_run:
        counts = zsh_module.run_bootstrap(dry_run=False)

    # subprocess.run should be called once per plugin (git clone) + 2 for autojump
    # (git clone + python3 install.py) = 3 + 2 = 5 calls
    assert mock_run.call_count == 5
    assert counts == {"installed": 4, "skipped": 0}


# ---------------------------------------------------------------------------
# check_zshrc
# ---------------------------------------------------------------------------

def test_check_zshrc_no_file(tmp_path, monkeypatch):
    monkeypatch.setattr(zsh_module, "HOME", tmp_path)
    assert zsh_module.check_zshrc() == []


def test_check_zshrc_all_plugins_present(tmp_path, monkeypatch):
    monkeypatch.setattr(zsh_module, "HOME", tmp_path)
    plugins_line = " ".join(zsh_module.EXPECTED_PLUGINS)
    zshrc = tmp_path / ".zshrc"
    zshrc.write_text(f"plugins=({plugins_line})\n")
    assert zsh_module.check_zshrc() == []


def test_check_zshrc_missing_some_plugins(tmp_path, monkeypatch):
    monkeypatch.setattr(zsh_module, "HOME", tmp_path)
    zshrc = tmp_path / ".zshrc"
    # Only include 'git' and 'copypath', leave out the rest
    zshrc.write_text("plugins=(git copypath)\n")
    missing = zsh_module.check_zshrc()
    expected_missing = sorted(zsh_module.EXPECTED_PLUGINS - {"git", "copypath"})
    assert missing == expected_missing


def test_check_zshrc_no_plugins_declaration(tmp_path, monkeypatch):
    monkeypatch.setattr(zsh_module, "HOME", tmp_path)
    zshrc = tmp_path / ".zshrc"
    zshrc.write_text("export ZSH=$HOME/.oh-my-zsh\nsource $ZSH/oh-my-zsh.sh\n")
    assert zsh_module.check_zshrc() == sorted(zsh_module.EXPECTED_PLUGINS)


def test_check_zshrc_skips_commented_lines(tmp_path, monkeypatch):
    monkeypatch.setattr(zsh_module, "HOME", tmp_path)
    zshrc = tmp_path / ".zshrc"
    # All plugins listed but inside a comment — should be treated as absent
    plugins_line = " ".join(zsh_module.EXPECTED_PLUGINS)
    zshrc.write_text(f"# plugins=({plugins_line})\nplugins=(git)\n")
    missing = zsh_module.check_zshrc()
    assert "git" not in missing
    # Other expected plugins should be missing
    for p in zsh_module.EXPECTED_PLUGINS - {"git"}:
        assert p in missing
