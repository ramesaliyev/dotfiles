"""Tests for src/core/files.py — sync_file in both directions."""

from __future__ import annotations

from pathlib import Path

from src.core.checksum import checksum
from src.core.events import FileConflict, FileCopied, FileSkipped, Warning
from src.core.files import sync_file

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _state(entries=None):
    return {"version": 1, "entries": entries or {}}


def _make_file(path: Path, content: bytes = b"content") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def _entry(src: Path, _dest: Path) -> dict:
    """State entry where src and dest are in sync."""
    cs = checksum(src)
    return {"src_rel": str(src), "src_checksum": cs, "dest_checksum": cs, "synced_at": "t"}


def _run(src, dest, state, *, force=False, dry_run=False):
    return list(sync_file(src, dest, state, force=force, dry_run=dry_run))


# ---------------------------------------------------------------------------
# src missing
# ---------------------------------------------------------------------------


def test_src_missing_yields_warning(tmp_path):
    src = tmp_path / "nonexistent.conf"
    dest = tmp_path / "dest.conf"
    events = _run(src, dest, _state())
    assert len(events) == 1
    assert isinstance(events[0], Warning)


# ---------------------------------------------------------------------------
# dest missing — new file
# ---------------------------------------------------------------------------


def test_dest_missing_copies_file(tmp_path):
    src = _make_file(tmp_path / "src.conf", b"hello")
    dest = tmp_path / "sub" / "dest.conf"
    state = _state()

    events = _run(src, dest, state)

    assert len(events) == 1
    assert isinstance(events[0], FileCopied)
    assert events[0].action == "copied"
    assert dest.read_bytes() == b"hello"
    assert str(dest) in state["entries"]


def test_dest_missing_dry_run_no_write(tmp_path):
    src = _make_file(tmp_path / "src.conf", b"hello")
    dest = tmp_path / "dest.conf"
    state = _state()

    events = _run(src, dest, state, dry_run=True)

    assert isinstance(events[0], FileCopied)
    assert not dest.exists()
    assert state["entries"] == {}


# ---------------------------------------------------------------------------
# dest exists, no state entry
# ---------------------------------------------------------------------------


def test_untracked_same_content_adopts_silently(tmp_path):
    src = _make_file(tmp_path / "src.conf", b"same")
    dest = _make_file(tmp_path / "dest.conf", b"same")
    state = _state()

    events = _run(src, dest, state)

    assert isinstance(events[0], FileSkipped)
    assert str(dest) in state["entries"]


def test_untracked_diff_content_force(tmp_path):
    src = _make_file(tmp_path / "src.conf", b"new")
    dest = _make_file(tmp_path / "dest.conf", b"old")
    state = _state()

    events = _run(src, dest, state, force=True)

    assert any(isinstance(e, FileCopied) and e.action == "overwritten" for e in events)
    assert dest.read_bytes() == b"new"


def test_untracked_diff_content_user_yes(monkeypatch, tmp_path):
    monkeypatch.setattr("builtins.input", lambda _: "Y")
    src = _make_file(tmp_path / "src.conf", b"new")
    dest = _make_file(tmp_path / "dest.conf", b"old")

    events = _run(src, dest, _state())

    assert any(isinstance(e, FileCopied) for e in events)
    assert dest.read_bytes() == b"new"


def test_untracked_diff_content_user_no(monkeypatch, tmp_path):
    monkeypatch.setattr("builtins.input", lambda _: "n")
    src = _make_file(tmp_path / "src.conf", b"new")
    dest = _make_file(tmp_path / "dest.conf", b"old")

    events = _run(src, dest, _state())

    assert any(isinstance(e, FileSkipped) and e.reason == "kept local" for e in events)
    assert dest.read_bytes() == b"old"


# ---------------------------------------------------------------------------
# dest exists, state entry present
# ---------------------------------------------------------------------------


def test_nothing_changed_skips(tmp_path):
    src = _make_file(tmp_path / "src.conf", b"v1")
    dest = _make_file(tmp_path / "dest.conf", b"v1")
    state = _state({str(dest): _entry(src, dest)})

    events = _run(src, dest, state)

    assert isinstance(events[0], FileSkipped)
    assert dest.read_bytes() == b"v1"


def test_only_src_changed_updates(tmp_path):
    src = _make_file(tmp_path / "src.conf", b"v1")
    dest = _make_file(tmp_path / "dest.conf", b"v1")
    entry = _entry(src, dest)
    src.write_bytes(b"v2")
    state = _state({str(dest): entry})

    events = _run(src, dest, state)

    assert isinstance(events[0], FileCopied)
    assert events[0].action == "updated"
    assert dest.read_bytes() == b"v2"


def test_only_dest_changed_warns(tmp_path):
    src = _make_file(tmp_path / "src.conf", b"v1")
    dest = _make_file(tmp_path / "dest.conf", b"v1")
    entry = _entry(src, dest)
    dest.write_bytes(b"local-tweak")
    state = _state({str(dest): entry})

    events = _run(src, dest, state)

    assert isinstance(events[0], Warning)
    assert dest.read_bytes() == b"local-tweak"


def test_both_changed_force(tmp_path):
    src = _make_file(tmp_path / "src.conf", b"v1")
    dest = _make_file(tmp_path / "dest.conf", b"v1")
    entry = _entry(src, dest)
    src.write_bytes(b"src-v2")
    dest.write_bytes(b"dest-v2")
    state = _state({str(dest): entry})

    events = _run(src, dest, state, force=True)

    assert any(isinstance(e, FileCopied) and e.action == "overwritten" for e in events)
    assert dest.read_bytes() == b"src-v2"


def test_both_changed_user_yes(monkeypatch, tmp_path):
    monkeypatch.setattr("builtins.input", lambda _: "Y")
    src = _make_file(tmp_path / "src.conf", b"v1")
    dest = _make_file(tmp_path / "dest.conf", b"v1")
    entry = _entry(src, dest)
    src.write_bytes(b"src-v2")
    dest.write_bytes(b"dest-v2")

    events = _run(src, dest, _state({str(dest): entry}))

    assert any(isinstance(e, FileCopied) for e in events)
    assert dest.read_bytes() == b"src-v2"


def test_both_changed_dry_run_no_overwrite(tmp_path):
    src = _make_file(tmp_path / "src.conf", b"v1")
    dest = _make_file(tmp_path / "dest.conf", b"v1")
    entry = _entry(src, dest)
    src.write_bytes(b"src-v2")
    dest.write_bytes(b"dest-v2")
    state = _state({str(dest): entry})

    events = _run(src, dest, state, dry_run=True)

    assert any(isinstance(e, FileConflict) for e in events)
    assert dest.read_bytes() == b"dest-v2"


# ---------------------------------------------------------------------------
# collect direction (src=machine, dest=repo) — same logic, reversed roles
# ---------------------------------------------------------------------------


def test_collect_direction_machine_changed_updates_repo(tmp_path):
    machine = _make_file(tmp_path / "machine" / ".tmux.conf", b"v1")
    repo = _make_file(tmp_path / "repo" / ".tmux.conf", b"v1")
    entry = _entry(machine, repo)
    machine.write_bytes(b"v2")  # machine changed — collect it
    state = _state({str(repo): entry})

    events = list(sync_file(machine, repo, state, force=False, dry_run=False))

    assert isinstance(events[0], FileCopied)
    assert events[0].action == "updated"
    assert repo.read_bytes() == b"v2"


def test_collect_direction_repo_changed_warns(tmp_path):
    machine = _make_file(tmp_path / "machine" / ".tmux.conf", b"v1")
    repo = _make_file(tmp_path / "repo" / ".tmux.conf", b"v1")
    entry = _entry(machine, repo)
    repo.write_bytes(b"repo-only-change")  # repo changed, machine didn't
    state = _state({str(repo): entry})

    events = list(sync_file(machine, repo, state, force=False, dry_run=False))

    assert isinstance(events[0], Warning)
    assert repo.read_bytes() == b"repo-only-change"
