"""Tests for scripts/modules/tmux.py — mapping structure and consistency."""

from __future__ import annotations

from pathlib import Path

from scripts.modules import tmux

HOME = Path.home()


# ---------------------------------------------------------------------------
# COLLECT_MAPPINGS
# ---------------------------------------------------------------------------


def test_collect_mappings_has_two_entries():
    assert len(tmux.COLLECT_MAPPINGS) == 2


def test_collect_mappings_structure():
    for entry in tmux.COLLECT_MAPPINGS:
        src, dest_rel = entry
        assert isinstance(src, Path)
        assert isinstance(dest_rel, str)


def test_collect_mappings_sources_under_home():
    for src, _ in tmux.COLLECT_MAPPINGS:
        assert str(src).startswith(str(HOME))


# ---------------------------------------------------------------------------
# BOOTSTRAP_MAPPINGS
# ---------------------------------------------------------------------------


def test_bootstrap_mappings_has_two_entries():
    assert len(tmux.BOOTSTRAP_MAPPINGS) == 2


def test_bootstrap_mappings_structure():
    for entry in tmux.BOOTSTRAP_MAPPINGS:
        repo_rel, dest = entry
        assert isinstance(repo_rel, str)
        assert isinstance(dest, Path)


def test_bootstrap_mappings_dests_under_home():
    for _, dest in tmux.BOOTSTRAP_MAPPINGS:
        assert str(dest).startswith(str(HOME))


# ---------------------------------------------------------------------------
# Symmetry: collect ↔ bootstrap are inverses
# ---------------------------------------------------------------------------


def test_collect_bootstrap_are_inverses():
    collect_pairs = {(str(src), dest_rel) for src, dest_rel in tmux.COLLECT_MAPPINGS}
    bootstrap_pairs = {(dest_rel, str(dest)) for dest_rel, dest in tmux.BOOTSTRAP_MAPPINGS}
    # Each collect (machine_path → repo_rel) should have a matching
    # bootstrap (repo_rel → machine_path)
    for machine_path, repo_rel in collect_pairs:
        assert (repo_rel, machine_path) in bootstrap_pairs


# ---------------------------------------------------------------------------
# Theme directories
# ---------------------------------------------------------------------------


def test_collect_themes_src_under_home():
    assert str(tmux.COLLECT_THEMES_SRC).startswith(str(HOME))


def test_bootstrap_themes_dest_under_home():
    assert str(tmux.BOOTSTRAP_THEMES_DEST).startswith(str(HOME))


def test_bootstrap_themes_src_rel_is_string():
    assert isinstance(tmux.BOOTSTRAP_THEMES_SRC_REL, str)


def test_collect_themes_dest_rel_is_string():
    assert isinstance(tmux.COLLECT_THEMES_DEST_REL, str)


# ---------------------------------------------------------------------------
# Metadata constants
# ---------------------------------------------------------------------------


def test_post_bootstrap_note_is_non_empty_string():
    assert isinstance(tmux.POST_BOOTSTRAP_NOTE, str)
    assert len(tmux.POST_BOOTSTRAP_NOTE) > 0


def test_readme_rel_is_string():
    assert isinstance(tmux.README_REL, str)
