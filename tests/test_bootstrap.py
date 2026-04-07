"""Tests for scripts/bootstrap.py — handle_file and print_module_note."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import scripts.bootstrap as bootstrap
from scripts.common import checksum


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_state(entries=None):
    return {"version": 1, "entries": entries or {}}


def _repo_rel(repo_root: Path, name: str) -> str:
    """Return a repo-relative path string for a file placed in repo_root."""
    return name


def _setup_repo_file(repo_root: Path, rel: str, content: bytes = b"content") -> Path:
    src = repo_root / rel
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_bytes(content)
    return src


def _run(monkeypatch, repo_root, repo_rel, dest, state, *, force=False, dry_run=False):
    monkeypatch.setattr(bootstrap, "REPO_ROOT", repo_root)
    return bootstrap.handle_file(repo_rel, dest, state, force=force, dry_run=dry_run)


# ---------------------------------------------------------------------------
# handle_file — destination does not exist
# ---------------------------------------------------------------------------

def test_handle_file_dest_missing(monkeypatch, tmp_path):
    repo_root = tmp_path / "repo"
    _setup_repo_file(repo_root, "foo.conf", b"hello")
    dest = tmp_path / "dest" / "foo.conf"
    state = _make_state()

    result = _run(monkeypatch, repo_root, "foo.conf", dest, state)

    assert result == "copied"
    assert dest.read_bytes() == b"hello"
    assert str(dest) in state["entries"]


def test_handle_file_dest_missing_dry_run(monkeypatch, tmp_path):
    repo_root = tmp_path / "repo"
    _setup_repo_file(repo_root, "foo.conf", b"hello")
    dest = tmp_path / "dest" / "foo.conf"
    state = _make_state()

    result = _run(monkeypatch, repo_root, "foo.conf", dest, state, dry_run=True)

    assert result == "copied"
    assert not dest.exists()
    assert state["entries"] == {}


# ---------------------------------------------------------------------------
# handle_file — repo file missing
# ---------------------------------------------------------------------------

def test_handle_file_repo_missing(monkeypatch, tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    dest = tmp_path / "foo.conf"
    state = _make_state()

    result = _run(monkeypatch, repo_root, "missing.conf", dest, state)

    assert result == "warned"


# ---------------------------------------------------------------------------
# handle_file — dest exists, no state entry
# ---------------------------------------------------------------------------

def test_handle_file_untracked_same_content(monkeypatch, tmp_path):
    repo_root = tmp_path / "repo"
    _setup_repo_file(repo_root, "foo.conf", b"same")
    dest = tmp_path / "foo.conf"
    dest.write_bytes(b"same")
    state = _make_state()

    result = _run(monkeypatch, repo_root, "foo.conf", dest, state)

    assert result == "skipped"
    # State should now track the file (silently adopted)
    assert str(dest) in state["entries"]


def test_handle_file_untracked_diff_content_force(monkeypatch, tmp_path):
    repo_root = tmp_path / "repo"
    _setup_repo_file(repo_root, "foo.conf", b"repo-version")
    dest = tmp_path / "foo.conf"
    dest.write_bytes(b"local-version")
    state = _make_state()

    result = _run(monkeypatch, repo_root, "foo.conf", dest, state, force=True)

    assert result == "copied"
    assert dest.read_bytes() == b"repo-version"


def test_handle_file_untracked_diff_content_user_yes(monkeypatch, tmp_path):
    monkeypatch.setattr("builtins.input", lambda _: "Y")
    repo_root = tmp_path / "repo"
    _setup_repo_file(repo_root, "foo.conf", b"repo-version")
    dest = tmp_path / "foo.conf"
    dest.write_bytes(b"local-version")
    state = _make_state()

    result = _run(monkeypatch, repo_root, "foo.conf", dest, state)

    assert result == "copied"
    assert dest.read_bytes() == b"repo-version"


def test_handle_file_untracked_diff_content_user_no(monkeypatch, tmp_path):
    monkeypatch.setattr("builtins.input", lambda _: "n")
    repo_root = tmp_path / "repo"
    _setup_repo_file(repo_root, "foo.conf", b"repo-version")
    dest = tmp_path / "foo.conf"
    dest.write_bytes(b"local-version")
    state = _make_state()

    result = _run(monkeypatch, repo_root, "foo.conf", dest, state)

    assert result == "warned"
    assert dest.read_bytes() == b"local-version"


# ---------------------------------------------------------------------------
# handle_file — dest exists, state entry present
# ---------------------------------------------------------------------------

def _make_entry(repo_root: Path, dest: Path, rel: str) -> dict:
    """Build a state entry where repo and dest are in sync."""
    cs = checksum(repo_root / rel)
    return {
        "repo_rel": rel,
        "repo_checksum": cs,
        "dest_checksum": cs,
        "bootstrapped_at": "2024-01-01T00:00:00+00:00",
    }


def test_handle_file_nothing_changed(monkeypatch, tmp_path):
    repo_root = tmp_path / "repo"
    _setup_repo_file(repo_root, "foo.conf", b"v1")
    dest = tmp_path / "foo.conf"
    dest.write_bytes(b"v1")
    entry = _make_entry(repo_root, dest, "foo.conf")
    state = _make_state({str(dest): entry})

    result = _run(monkeypatch, repo_root, "foo.conf", dest, state)

    assert result == "skipped"
    assert dest.read_bytes() == b"v1"


def test_handle_file_only_repo_changed(monkeypatch, tmp_path):
    repo_root = tmp_path / "repo"
    src = _setup_repo_file(repo_root, "foo.conf", b"v1")
    dest = tmp_path / "foo.conf"
    dest.write_bytes(b"v1")
    old_cs = checksum(src)

    # Now update only the repo file
    src.write_bytes(b"v2")
    state = _make_state({
        str(dest): {
            "repo_rel": "foo.conf",
            "repo_checksum": old_cs,   # recorded v1
            "dest_checksum": old_cs,   # dest was v1 too
            "bootstrapped_at": "2024-01-01T00:00:00+00:00",
        }
    })

    result = _run(monkeypatch, repo_root, "foo.conf", dest, state)

    assert result == "copied"
    assert dest.read_bytes() == b"v2"


def test_handle_file_only_dest_changed(monkeypatch, tmp_path):
    repo_root = tmp_path / "repo"
    src = _setup_repo_file(repo_root, "foo.conf", b"v1")
    dest = tmp_path / "foo.conf"
    dest.write_bytes(b"v1")
    old_cs = checksum(src)

    # Now modify only dest
    dest.write_bytes(b"local-tweak")
    state = _make_state({
        str(dest): {
            "repo_rel": "foo.conf",
            "repo_checksum": old_cs,
            "dest_checksum": old_cs,  # recorded original
            "bootstrapped_at": "2024-01-01T00:00:00+00:00",
        }
    })

    result = _run(monkeypatch, repo_root, "foo.conf", dest, state)

    assert result == "warned"
    assert dest.read_bytes() == b"local-tweak"


def test_handle_file_both_changed_force(monkeypatch, tmp_path):
    repo_root = tmp_path / "repo"
    src = _setup_repo_file(repo_root, "foo.conf", b"v1")
    dest = tmp_path / "foo.conf"
    dest.write_bytes(b"v1")
    old_cs = checksum(src)

    src.write_bytes(b"repo-v2")
    dest.write_bytes(b"local-v2")
    state = _make_state({
        str(dest): {
            "repo_rel": "foo.conf",
            "repo_checksum": old_cs,
            "dest_checksum": old_cs,
            "bootstrapped_at": "2024-01-01T00:00:00+00:00",
        }
    })

    result = _run(monkeypatch, repo_root, "foo.conf", dest, state, force=True)

    assert result == "copied"
    assert dest.read_bytes() == b"repo-v2"


def test_handle_file_both_changed_user_yes(monkeypatch, tmp_path):
    monkeypatch.setattr("builtins.input", lambda _: "Y")
    repo_root = tmp_path / "repo"
    src = _setup_repo_file(repo_root, "foo.conf", b"v1")
    dest = tmp_path / "foo.conf"
    dest.write_bytes(b"v1")
    old_cs = checksum(src)

    src.write_bytes(b"repo-v2")
    dest.write_bytes(b"local-v2")
    state = _make_state({
        str(dest): {
            "repo_rel": "foo.conf",
            "repo_checksum": old_cs,
            "dest_checksum": old_cs,
            "bootstrapped_at": "2024-01-01T00:00:00+00:00",
        }
    })

    result = _run(monkeypatch, repo_root, "foo.conf", dest, state)

    assert result == "copied"
    assert dest.read_bytes() == b"repo-v2"


def test_handle_file_both_changed_dry_run(monkeypatch, tmp_path):
    repo_root = tmp_path / "repo"
    src = _setup_repo_file(repo_root, "foo.conf", b"v1")
    dest = tmp_path / "foo.conf"
    dest.write_bytes(b"v1")
    old_cs = checksum(src)

    src.write_bytes(b"repo-v2")
    dest.write_bytes(b"local-v2")
    state = _make_state({
        str(dest): {
            "repo_rel": "foo.conf",
            "repo_checksum": old_cs,
            "dest_checksum": old_cs,
            "bootstrapped_at": "2024-01-01T00:00:00+00:00",
        }
    })

    # dry_run: should not prompt and should not overwrite
    result = _run(monkeypatch, repo_root, "foo.conf", dest, state, dry_run=True)

    assert result == "warned"
    assert dest.read_bytes() == b"local-v2"


# ---------------------------------------------------------------------------
# print_module_note
# ---------------------------------------------------------------------------

def test_print_module_note_with_note_and_readme(monkeypatch, tmp_path, capsys):
    readme = tmp_path / "dotfiles" / "tmux" / "README.md"
    readme.parent.mkdir(parents=True)
    readme.write_text("# readme")
    monkeypatch.setattr(bootstrap, "REPO_ROOT", tmp_path)

    module = SimpleNamespace(
        POST_BOOTSTRAP_NOTE="Do the thing.\nSecond line.",
        README_REL="dotfiles/tmux/README.md",
    )
    bootstrap.print_module_note(module)

    out = capsys.readouterr().out
    assert "Do the thing." in out
    assert "Second line." in out
    assert "dotfiles/tmux/README.md" in out


def test_print_module_note_missing_readme(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(bootstrap, "REPO_ROOT", tmp_path)

    module = SimpleNamespace(
        POST_BOOTSTRAP_NOTE="Note here.",
        README_REL="dotfiles/tmux/README.md",  # file does NOT exist
    )
    bootstrap.print_module_note(module)

    out = capsys.readouterr().out
    assert "Note here." in out
    assert "See:" not in out


def test_print_module_note_no_note(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(bootstrap, "REPO_ROOT", tmp_path)

    module = SimpleNamespace()  # no POST_BOOTSTRAP_NOTE, no README_REL
    bootstrap.print_module_note(module)

    out = capsys.readouterr().out
    assert out == ""
