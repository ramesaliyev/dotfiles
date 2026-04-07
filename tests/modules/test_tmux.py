"""Tests for src/modules/tmux — config and module behavior."""

from __future__ import annotations

from pathlib import Path

import yaml

HOME = Path.home()
CONFIG_PATH = Path(__file__).parent.parent.parent / "src" / "modules" / "tmux" / "config.yaml"


def _cfg():
    with CONFIG_PATH.open() as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# config.yaml structure
# ---------------------------------------------------------------------------


def test_config_has_files_list():
    assert isinstance(_cfg()["files"], list)
    assert len(_cfg()["files"]) >= 1


def test_each_file_entry_has_machine_and_repo():
    for entry in _cfg()["files"]:
        assert "machine" in entry
        assert "repo" in entry
        assert isinstance(entry["machine"], str)
        assert isinstance(entry["repo"], str)


def test_machine_paths_start_with_tilde():
    for entry in _cfg()["files"]:
        assert entry["machine"].startswith("~")


def test_machine_paths_expand_to_home():
    for entry in _cfg()["files"]:
        expanded = Path(entry["machine"]).expanduser()
        assert str(expanded).startswith(str(HOME))


def test_repo_paths_are_relative():
    for entry in _cfg()["files"]:
        assert not entry["repo"].startswith("/")


def test_config_has_readme():
    assert isinstance(_cfg().get("readme"), str)


def test_config_has_post_bootstrap_note():
    assert isinstance(_cfg().get("post_bootstrap_note"), str)
    assert len(_cfg()["post_bootstrap_note"]) > 0


# ---------------------------------------------------------------------------
# Symmetry: machine↔repo are inverse mappings
# ---------------------------------------------------------------------------


def test_all_machine_repo_pairs_unique():
    files = _cfg()["files"]
    machines = [e["machine"] for e in files]
    repos = [e["repo"] for e in files]
    assert len(machines) == len(set(machines)), "duplicate machine paths"
    assert len(repos) == len(set(repos)), "duplicate repo paths"


# ---------------------------------------------------------------------------
# TmuxModule bootstrap/collect yield correct event types
# ---------------------------------------------------------------------------


def test_bootstrap_yields_module_start_and_end(monkeypatch, tmp_path):
    from argparse import Namespace

    from src.modules.tmux.module import TmuxModule
    from src.ui.events import ModuleEnd, ModuleStart

    # Create dummy repo files so sync_file doesn't warn
    cfg = _cfg()
    for entry in cfg["files"]:
        repo_file = tmp_path / entry["repo"]
        repo_file.parent.mkdir(parents=True, exist_ok=True)
        repo_file.write_bytes(b"content")

    import src.modules.tmux.module as tmux_mod

    monkeypatch.setattr(tmux_mod, "REPO_ROOT", tmp_path)

    args = Namespace(force=False, dry_run=True, verbose=False)
    state = {"version": 1, "entries": {}}
    events = list(TmuxModule().bootstrap(args, state))

    assert isinstance(events[0], ModuleStart)
    assert events[0].name == "tmux"
    assert isinstance(events[-1], ModuleEnd)
    assert events[-1].name == "tmux"


def test_collect_yields_module_start_and_end(monkeypatch, tmp_path):
    from argparse import Namespace

    import src.modules.tmux.module as tmux_mod
    from src.modules.tmux.module import TmuxModule
    from src.ui.events import ModuleEnd, ModuleStart

    monkeypatch.setattr(tmux_mod, "REPO_ROOT", tmp_path)

    args = Namespace(force=False, dry_run=True, verbose=False)
    state = {"version": 1, "entries": {}}
    events = list(TmuxModule().collect(args, state))

    assert isinstance(events[0], ModuleStart)
    assert isinstance(events[-1], ModuleEnd)
