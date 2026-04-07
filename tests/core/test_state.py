"""Tests for src/core/state.py"""

from __future__ import annotations

import json

from src.core import state as state_mod


def _patch(monkeypatch, tmp_path):
    path = tmp_path / "state.json"
    monkeypatch.setattr(state_mod, "STATE_FILE", path)
    return path


# ---------------------------------------------------------------------------
# load_state
# ---------------------------------------------------------------------------


def test_load_state_missing_file(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    assert state_mod.load_state() == {"version": 1, "entries": {}}


def test_load_state_existing_file(monkeypatch, tmp_path):
    path = _patch(monkeypatch, tmp_path)
    data = {
        "version": 1,
        "entries": {
            "/foo": {
                "src_rel": "foo",
                "src_checksum": "abc",
                "dest_checksum": "abc",
                "synced_at": "2024-01-01T00:00:00+00:00",
            },
        },
    }
    path.write_text(json.dumps(data))
    assert state_mod.load_state() == data


# ---------------------------------------------------------------------------
# save_state
# ---------------------------------------------------------------------------


def test_save_state_creates_parent_dir(monkeypatch, tmp_path):
    state_file = tmp_path / "nested" / "dir" / "state.json"
    monkeypatch.setattr(state_mod, "STATE_FILE", state_file)
    state_mod.save_state({"version": 1, "entries": {}})
    assert state_file.exists()


def test_save_state_writes_json_with_trailing_newline(monkeypatch, tmp_path):
    path = _patch(monkeypatch, tmp_path)
    state = {"version": 1, "entries": {}}
    state_mod.save_state(state)
    raw = path.read_text()
    assert raw.endswith("\n")
    assert json.loads(raw) == state


def test_save_load_round_trip(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    original = {
        "version": 1,
        "entries": {
            "/home/user/.tmux.conf": {
                "src_rel": "dotfiles/tmux/.tmux.conf",
                "src_checksum": "deadbeef",
                "dest_checksum": "deadbeef",
                "synced_at": "2024-06-01T12:00:00+00:00",
            },
        },
    }
    state_mod.save_state(original)
    assert state_mod.load_state() == original
