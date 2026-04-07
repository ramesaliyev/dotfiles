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


def test_bootstrap_yields_module_start_and_end():
    from src.core.events import ModuleEnd, ModuleStart
    from src.modules.tmux.module import TmuxModule

    events = list(TmuxModule().bootstrap())

    assert isinstance(events[0], ModuleStart)
    assert events[0].name == "tmux"
    assert isinstance(events[-1], ModuleEnd)
    assert events[-1].name == "tmux"
    assert not hasattr(events[-1], "counts")


def test_bootstrap_yields_sync_file_events():
    from src.core.events import SyncFile
    from src.modules.tmux.module import TmuxModule

    events = list(TmuxModule().bootstrap())

    sync_events = [e for e in events if isinstance(e, SyncFile)]
    assert len(sync_events) == len(_cfg()["files"])


def test_collect_yields_module_start_and_end():
    from src.core.events import ModuleEnd, ModuleStart
    from src.modules.tmux.module import TmuxModule

    events = list(TmuxModule().collect())

    assert isinstance(events[0], ModuleStart)
    assert isinstance(events[-1], ModuleEnd)
