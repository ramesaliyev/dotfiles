"""Tests for src/runner.py"""

from __future__ import annotations

from src.core.events import (
    Done,
    FileConflict,
    FileCopied,
    GitClone,
    Info,
    ModuleEnd,
    ModuleStart,
    Skipped,
    SubprocessRun,
    Warning,
)
from src.runner import run


def _state():
    return {"version": 1, "entries": {}}


def _run(events, *, verbose=False, dry_run=False):
    return run(iter(events), state=_state(), force=False, dry_run=dry_run, verbose=verbose)


def _end(name="tmux"):
    return ModuleEnd(name, note=None)


# ---------------------------------------------------------------------------
# FileCopied
# ---------------------------------------------------------------------------


def test_file_copied_prints_action(tmp_path, capsys):
    dest = tmp_path / "foo.conf"
    event = FileCopied(src=tmp_path / "src.conf", dest=dest, action="copied")
    _run([ModuleStart("tmux"), event, _end()])
    assert "copied" in capsys.readouterr().out


def test_file_copied_dry_run_still_prints(tmp_path, capsys):
    dest = tmp_path / "foo.conf"
    event = FileCopied(src=tmp_path / "src.conf", dest=dest, action="copied")
    _run([ModuleStart("tmux"), event, _end()], dry_run=True)
    assert "copied" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Skipped -- file skipped
# ---------------------------------------------------------------------------


def test_file_skipped_hidden_by_default(tmp_path, capsys):
    dest = tmp_path / "foo.conf"
    _run([ModuleStart("tmux"), Skipped(name=str(dest), details="unchanged"), _end()])
    # Per-item line hidden; only the summary count should mention "skipped"
    out = capsys.readouterr().out
    assert str(dest) not in out


def test_file_skipped_visible_with_verbose(tmp_path, capsys):
    dest = tmp_path / "foo.conf"
    _run([ModuleStart("tmux"), Skipped(name=str(dest), details="unchanged"), _end()], verbose=True)
    assert str(dest) in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Warning / FileConflict
# ---------------------------------------------------------------------------


def test_warning_goes_to_stderr(capsys):
    _run([ModuleStart("tmux"), Warning("something bad"), _end()])
    assert "something bad" in capsys.readouterr().err


def test_warning_multiline_each_line_prefixed(capsys):
    _run([ModuleStart("tmux"), Warning("line one\nline two"), _end()])
    err = capsys.readouterr().err
    assert "! line one" in err
    assert "! line two" in err


def test_conflict_goes_to_stderr(tmp_path, capsys):
    event = FileConflict(dest=tmp_path / "foo.conf", description="both changed")
    _run([ModuleStart("tmux"), event, _end()])
    assert "conflict" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# Info
# ---------------------------------------------------------------------------


def test_info_goes_to_stdout(capsys):
    _run([ModuleStart("tmux"), Info("just letting you know"), _end()])
    out = capsys.readouterr().out
    assert "just letting you know" in out


def test_info_not_counted_as_warned():
    counts = _run([ModuleStart("tmux"), Info("just letting you know"), _end()])
    assert counts["warned"] == 0


# ---------------------------------------------------------------------------
# SubprocessRun
# ---------------------------------------------------------------------------


def test_subprocess_run_is_executed(monkeypatch):
    import subprocess as sp

    calls = []
    monkeypatch.setattr(sp, "run", lambda *a, **kw: calls.append((a, kw)))
    _run([SubprocessRun(["echo", "hi"])])
    assert len(calls) == 1
    assert calls[0][0][0] == ["echo", "hi"]


def test_subprocess_run_skipped_on_dry_run(monkeypatch):
    import subprocess as sp

    calls = []
    monkeypatch.setattr(sp, "run", lambda *a, **kw: calls.append((a, kw)))
    _run([SubprocessRun(["echo", "hi"])], dry_run=True)
    assert len(calls) == 0


def test_subprocess_run_not_counted(monkeypatch):
    import subprocess as sp

    monkeypatch.setattr(sp, "run", lambda *_a, **_kw: None)
    counts = _run([ModuleStart("tmux"), SubprocessRun(["echo", "hi"]), _end()])
    assert counts["copied"] == 0
    assert counts["skipped"] == 0
    assert counts["warned"] == 0


# ---------------------------------------------------------------------------
# ModuleStart / ModuleEnd
# ---------------------------------------------------------------------------


def test_module_start_prints_name(capsys):
    _run([ModuleStart("tmux")])
    assert "[tmux]" in capsys.readouterr().out


def test_module_end_prints_counts(tmp_path, capsys):
    dest = tmp_path / "foo.conf"
    _run(
        [
            ModuleStart("tmux"),
            FileCopied(src=dest, dest=dest, action="copied"),
            FileCopied(src=dest, dest=dest, action="copied"),
            Skipped(name=str(dest), details="unchanged"),
            _end(),
        ]
    )
    out = capsys.readouterr().out
    assert "2 copied" in out
    assert "1 skipped" in out


def test_module_end_prints_note(capsys):
    _run(
        [
            ModuleStart("tmux"),
            ModuleEnd("tmux", "Do the thing."),
        ]
    )
    assert "Do the thing." in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Done / Skipped
# ---------------------------------------------------------------------------


def test_copy_done_prints_name(capsys):
    _run([ModuleStart("tmux"), Done("zsh-autosuggestions"), _end()])
    assert "zsh-autosuggestions" in capsys.readouterr().out


def test_copy_done_dry_run_still_prints(capsys):
    _run([ModuleStart("tmux"), Done("zsh-autosuggestions"), _end()], dry_run=True)
    assert "zsh-autosuggestions" in capsys.readouterr().out


def test_copy_skipped_hidden_by_default(capsys):
    _run([ModuleStart("tmux"), Skipped("zsh-autosuggestions"), _end()])
    assert "zsh-autosuggestions" not in capsys.readouterr().out


def test_copy_skipped_visible_with_verbose(capsys):
    _run([ModuleStart("tmux"), Skipped("zsh-autosuggestions"), _end()], verbose=True)
    assert "zsh-autosuggestions" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# GitClone
# ---------------------------------------------------------------------------


def test_git_clone_runs_subprocess(monkeypatch, tmp_path):
    import subprocess as sp

    calls = []
    monkeypatch.setattr(sp, "run", lambda *a, **kw: calls.append((a, kw)))
    dest = tmp_path / "plugin"
    _run([GitClone(url="https://github.com/example/repo", dest=dest)])
    assert len(calls) == 1
    assert calls[0][0][0] == ["git", "clone", "https://github.com/example/repo", str(dest)]


def test_git_clone_dry_run_no_subprocess(monkeypatch, tmp_path):
    import subprocess as sp

    calls = []
    monkeypatch.setattr(sp, "run", lambda *a, **kw: calls.append((a, kw)))
    _run([GitClone(url="https://github.com/example/repo", dest=tmp_path / "plugin")], dry_run=True)
    assert len(calls) == 0


# ---------------------------------------------------------------------------
# Total counts returned
# ---------------------------------------------------------------------------


def test_run_returns_total_counts(tmp_path):
    dest = tmp_path / "foo.conf"
    counts = _run(
        [
            ModuleStart("tmux"),
            FileCopied(src=tmp_path / "src.conf", dest=dest, action="copied"),
            Skipped(name=str(dest), details="unchanged"),
            Warning("oops"),
            _end(),
        ]
    )
    assert counts == {"copied": 1, "skipped": 1, "warned": 1}
