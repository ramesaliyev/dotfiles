"""Tests for src/ui/renderer.py"""

from __future__ import annotations

from src.ui.events import (
    FileConflict,
    FileCopied,
    FileSkipped,
    ModuleEnd,
    ModuleStart,
    PluginInstalled,
    PluginSkipped,
    PluginsMissing,
    Warning,
)
from src.ui.renderer import render


def _render(events, *, verbose=False):
    return render(iter(events), verbose=verbose)


# ---------------------------------------------------------------------------
# FileCopied
# ---------------------------------------------------------------------------


def test_file_copied_prints_action(tmp_path, capsys):
    dest = tmp_path / "foo.conf"
    _render([FileCopied(src=tmp_path / "src.conf", dest=dest, action="copied", dry_run=False)])
    assert "copied" in capsys.readouterr().out


def test_file_copied_dry_run_shows_prefix(tmp_path, capsys):
    dest = tmp_path / "foo.conf"
    _render([FileCopied(src=tmp_path / "src.conf", dest=dest, action="copied", dry_run=True)])
    assert "[dry-run]" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# FileSkipped
# ---------------------------------------------------------------------------


def test_file_skipped_hidden_by_default(tmp_path, capsys):
    _render([FileSkipped(dest=tmp_path / "foo.conf", reason="unchanged")])
    assert capsys.readouterr().out == ""


def test_file_skipped_visible_with_verbose(tmp_path, capsys):
    _render([FileSkipped(dest=tmp_path / "foo.conf", reason="unchanged")], verbose=True)
    assert "skipped" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Warning / FileConflict
# ---------------------------------------------------------------------------


def test_warning_goes_to_stderr(capsys):
    _render([Warning("something bad")])
    assert "something bad" in capsys.readouterr().err


def test_conflict_goes_to_stderr(tmp_path, capsys):
    _render([FileConflict(dest=tmp_path / "foo.conf", description="both changed")])
    assert "conflict" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# ModuleStart / ModuleEnd
# ---------------------------------------------------------------------------


def test_module_start_prints_name(capsys):
    _render([ModuleStart("tmux")])
    assert "[tmux]" in capsys.readouterr().out


def test_module_end_prints_counts(capsys):
    _render(
        [
            ModuleStart("tmux"),
            ModuleEnd("tmux", {"copied": 2, "skipped": 1, "warned": 0}, note=None, readme_rel=None),
        ]
    )
    out = capsys.readouterr().out
    assert "2 copied" in out
    assert "1 skipped" in out


def test_module_end_prints_note(capsys):
    _render(
        [
            ModuleStart("tmux"),
            ModuleEnd("tmux", {"copied": 0, "skipped": 0, "warned": 0}, "Do the thing.", None),
        ]
    )
    assert "Do the thing." in capsys.readouterr().out


def test_module_end_readme_shown_when_exists(monkeypatch, tmp_path, capsys):
    from src.ui import renderer

    monkeypatch.setattr(renderer, "REPO_ROOT", tmp_path)
    readme = tmp_path / "dotfiles" / "tmux" / "README.md"
    readme.parent.mkdir(parents=True)
    readme.write_text("# readme")

    _render(
        [
            ModuleStart("tmux"),
            ModuleEnd(
                "tmux", {"copied": 0, "skipped": 0, "warned": 0}, None, "dotfiles/tmux/README.md"
            ),
        ]
    )
    assert "dotfiles/tmux/README.md" in capsys.readouterr().out


def test_module_end_readme_hidden_when_missing(monkeypatch, tmp_path, capsys):
    from src.ui import renderer

    monkeypatch.setattr(renderer, "REPO_ROOT", tmp_path)

    _render(
        [
            ModuleStart("tmux"),
            ModuleEnd(
                "tmux", {"copied": 0, "skipped": 0, "warned": 0}, None, "dotfiles/tmux/README.md"
            ),
        ]
    )
    assert "See:" not in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Plugins
# ---------------------------------------------------------------------------


def test_plugin_installed_prints_name(capsys):
    _render([PluginInstalled("zsh-autosuggestions", dry_run=False)])
    assert "zsh-autosuggestions" in capsys.readouterr().out


def test_plugin_skipped_hidden_by_default(capsys):
    _render([PluginSkipped("zsh-autosuggestions")])
    assert capsys.readouterr().out == ""


def test_plugins_missing_goes_to_stderr(capsys):
    _render([PluginsMissing(["autojump", "you-should-use"])])
    err = capsys.readouterr().err
    assert "autojump" in err
    assert "you-should-use" in err


# ---------------------------------------------------------------------------
# Total counts returned
# ---------------------------------------------------------------------------


def test_render_returns_total_counts(tmp_path):
    dest = tmp_path / "foo.conf"
    counts = _render(
        [
            ModuleStart("tmux"),
            FileCopied(src=tmp_path / "src.conf", dest=dest, action="copied", dry_run=False),
            FileSkipped(dest=dest, reason="unchanged"),
            Warning("oops"),
            ModuleEnd("tmux", {"copied": 1, "skipped": 1, "warned": 1}, note=None, readme_rel=None),
        ]
    )
    assert counts == {"copied": 1, "skipped": 1, "warned": 1}
