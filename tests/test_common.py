"""Tests for scripts/common.py"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

import scripts.common as common


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _patch_state_file(monkeypatch, tmp_path):
    state_file = tmp_path / "state.json"
    monkeypatch.setattr(common, "STATE_FILE", state_file)
    return state_file


# ---------------------------------------------------------------------------
# load_state
# ---------------------------------------------------------------------------

def test_load_state_missing_file(monkeypatch, tmp_path):
    _patch_state_file(monkeypatch, tmp_path)
    state = common.load_state()
    assert state == {"version": 1, "entries": {}}


def test_load_state_existing_file(monkeypatch, tmp_path):
    state_file = _patch_state_file(monkeypatch, tmp_path)
    data = {"version": 1, "entries": {"/foo": {"repo_rel": "foo", "repo_checksum": "abc", "dest_checksum": "abc", "bootstrapped_at": "2024-01-01T00:00:00+00:00"}}}
    state_file.write_text(json.dumps(data))
    assert common.load_state() == data


# ---------------------------------------------------------------------------
# save_state
# ---------------------------------------------------------------------------

def test_save_state_creates_parent_dir(monkeypatch, tmp_path):
    state_file = tmp_path / "nested" / "dir" / "state.json"
    monkeypatch.setattr(common, "STATE_FILE", state_file)
    common.save_state({"version": 1, "entries": {}})
    assert state_file.exists()


def test_save_state_writes_json_with_trailing_newline(monkeypatch, tmp_path):
    state_file = _patch_state_file(monkeypatch, tmp_path)
    state = {"version": 1, "entries": {}}
    common.save_state(state)
    raw = state_file.read_text()
    assert raw.endswith("\n")
    assert json.loads(raw) == state


def test_save_load_round_trip(monkeypatch, tmp_path):
    _patch_state_file(monkeypatch, tmp_path)
    original = {
        "version": 1,
        "entries": {
            "/home/user/.tmux.conf": {
                "repo_rel": "dotfiles/tmux/.tmux.conf",
                "repo_checksum": "deadbeef",
                "dest_checksum": "deadbeef",
                "bootstrapped_at": "2024-06-01T12:00:00+00:00",
            }
        },
    }
    common.save_state(original)
    assert common.load_state() == original


# ---------------------------------------------------------------------------
# checksum
# ---------------------------------------------------------------------------

def test_checksum_deterministic(tmp_path):
    f = tmp_path / "file.txt"
    f.write_bytes(b"hello world")
    assert common.checksum(f) == common.checksum(f)


def test_checksum_differs_for_different_content(tmp_path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_bytes(b"hello")
    b.write_bytes(b"world")
    assert common.checksum(a) != common.checksum(b)


def test_checksum_is_sha256(tmp_path):
    f = tmp_path / "file.txt"
    content = b"test content"
    f.write_bytes(content)
    expected = hashlib.sha256(content).hexdigest()
    assert common.checksum(f) == expected


# ---------------------------------------------------------------------------
# now_iso
# ---------------------------------------------------------------------------

def test_now_iso_is_utc_iso_string():
    result = common.now_iso()
    dt = datetime.fromisoformat(result)
    assert dt.tzinfo is not None
    assert dt.tzinfo == timezone.utc


# ---------------------------------------------------------------------------
# warn / info
# ---------------------------------------------------------------------------

def test_warn_goes_to_stderr_with_prefix(capsys):
    common.warn("something wrong")
    captured = capsys.readouterr()
    assert captured.err == "  ! something wrong\n"
    assert captured.out == ""


def test_info_goes_to_stdout_with_prefix(capsys):
    common.info("all good")
    captured = capsys.readouterr()
    assert captured.out == "  all good\n"
    assert captured.err == ""


# ---------------------------------------------------------------------------
# ask_overwrite
# ---------------------------------------------------------------------------

def test_ask_overwrite_enter_returns_true(monkeypatch, tmp_path):
    monkeypatch.setattr("builtins.input", lambda _: "")
    assert common.ask_overwrite(tmp_path / "file") is True


def test_ask_overwrite_y_returns_true(monkeypatch, tmp_path):
    monkeypatch.setattr("builtins.input", lambda _: "Y")
    assert common.ask_overwrite(tmp_path / "file") is True


def test_ask_overwrite_n_returns_false(monkeypatch, tmp_path):
    monkeypatch.setattr("builtins.input", lambda _: "n")
    assert common.ask_overwrite(tmp_path / "file") is False


def test_ask_overwrite_eoferror_returns_false(monkeypatch, tmp_path):
    def raise_eof(_):
        raise EOFError
    monkeypatch.setattr("builtins.input", raise_eof)
    assert common.ask_overwrite(tmp_path / "file") is False
