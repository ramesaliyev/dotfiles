"""Tests for scripts/collect.py — collect_file and collect_dir."""

from __future__ import annotations

from scripts import collect

# ---------------------------------------------------------------------------
# collect_file
# ---------------------------------------------------------------------------


def test_collect_file_src_exists(monkeypatch, tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    monkeypatch.setattr(collect, "REPO_ROOT", repo_root)

    src = tmp_path / "machine" / "foo.conf"
    src.parent.mkdir()
    src.write_bytes(b"config content")

    collect.collect_file(src, "dotfiles/foo.conf")

    dest = repo_root / "dotfiles" / "foo.conf"
    assert dest.exists()
    assert dest.read_bytes() == b"config content"


def test_collect_file_src_missing(monkeypatch, tmp_path, capsys):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    monkeypatch.setattr(collect, "REPO_ROOT", repo_root)

    src = tmp_path / "nonexistent.conf"

    collect.collect_file(src, "dotfiles/foo.conf")

    dest = repo_root / "dotfiles" / "foo.conf"
    assert not dest.exists()
    assert "not found" in capsys.readouterr().err


def test_collect_file_creates_parent_dirs(monkeypatch, tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    monkeypatch.setattr(collect, "REPO_ROOT", repo_root)

    src = tmp_path / "foo.conf"
    src.write_bytes(b"data")

    collect.collect_file(src, "a/b/c/foo.conf")

    assert (repo_root / "a" / "b" / "c" / "foo.conf").exists()


# ---------------------------------------------------------------------------
# collect_dir
# ---------------------------------------------------------------------------


def test_collect_dir_exists_with_sh_files(monkeypatch, tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    monkeypatch.setattr(collect, "REPO_ROOT", repo_root)

    src_dir = tmp_path / "themes"
    src_dir.mkdir()
    (src_dir / "default.sh").write_bytes(b"theme1")
    (src_dir / "dark.sh").write_bytes(b"theme2")

    collect.collect_dir(src_dir, "dotfiles/themes")

    dest_dir = repo_root / "dotfiles" / "themes"
    assert (dest_dir / "default.sh").read_bytes() == b"theme1"
    assert (dest_dir / "dark.sh").read_bytes() == b"theme2"


def test_collect_dir_missing(monkeypatch, tmp_path, capsys):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    monkeypatch.setattr(collect, "REPO_ROOT", repo_root)

    src_dir = tmp_path / "nonexistent_dir"

    collect.collect_dir(src_dir, "dotfiles/themes")

    assert "not found" in capsys.readouterr().err


def test_collect_dir_ignores_non_sh_files(monkeypatch, tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    monkeypatch.setattr(collect, "REPO_ROOT", repo_root)

    src_dir = tmp_path / "themes"
    src_dir.mkdir()
    (src_dir / "theme.sh").write_bytes(b"shell theme")
    (src_dir / "readme.md").write_bytes(b"docs")
    (src_dir / "data.json").write_bytes(b"{}")

    collect.collect_dir(src_dir, "dotfiles/themes")

    dest_dir = repo_root / "dotfiles" / "themes"
    assert (dest_dir / "theme.sh").exists()
    assert not (dest_dir / "readme.md").exists()
    assert not (dest_dir / "data.json").exists()
