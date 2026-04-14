"""Tests for src/core/packages.py — install_package handler."""

from __future__ import annotations

import src.core.packages as pkg_mod
from src.core.events import InstallDone, InstallPackage, InstallSkipped, Warning
from src.core.packages import install_package


def _run(event, *, dry_run=False):
    return list(install_package(event, dry_run=dry_run))


# ---------------------------------------------------------------------------
# Already installed
# ---------------------------------------------------------------------------


def test_already_installed_skips(monkeypatch):
    monkeypatch.setattr(
        pkg_mod.shutil, "which", lambda name: "/usr/bin/autojump" if name == "autojump" else None
    )
    events = _run(InstallPackage(name="autojump"))
    assert events == [InstallSkipped("autojump")]


# ---------------------------------------------------------------------------
# Install via a specific package manager
# ---------------------------------------------------------------------------


def test_install_via_brew(monkeypatch):
    calls = []

    def fake_which(name):
        return "/usr/local/bin/brew" if name == "brew" else None

    def fake_run(cmd, **_kwargs):
        calls.append(cmd)

    monkeypatch.setattr(pkg_mod.shutil, "which", fake_which)
    monkeypatch.setattr(pkg_mod.subprocess, "run", fake_run)

    events = _run(InstallPackage(name="autojump", managers={"brew": "autojump"}))

    assert events == [InstallDone("autojump")]
    assert calls == [["brew", "install", "autojump"]]


def test_install_via_apt(monkeypatch):
    calls = []

    def fake_which(name):
        return "/usr/bin/apt-get" if name == "apt-get" else None

    def fake_run(cmd, **_kwargs):
        calls.append(cmd)

    monkeypatch.setattr(pkg_mod.shutil, "which", fake_which)
    monkeypatch.setattr(pkg_mod.subprocess, "run", fake_run)

    events = _run(InstallPackage(name="autojump", managers={"apt": "autojump"}))

    assert events == [InstallDone("autojump")]
    assert calls == [["apt-get", "install", "-y", "autojump"]]


# ---------------------------------------------------------------------------
# managers=None uses name for every PM
# ---------------------------------------------------------------------------


def test_managers_none_uses_name_for_all(monkeypatch):
    calls = []

    def fake_which(name):
        return "/usr/local/bin/brew" if name == "brew" else None

    def fake_run(cmd, **_kwargs):
        calls.append(cmd)

    monkeypatch.setattr(pkg_mod.shutil, "which", fake_which)
    monkeypatch.setattr(pkg_mod.subprocess, "run", fake_run)

    events = _run(InstallPackage(name="mypkg"))  # managers=None

    assert events == [InstallDone("mypkg")]
    assert calls == [["brew", "install", "mypkg"]]


# ---------------------------------------------------------------------------
# managers dict can override the package name per PM
# ---------------------------------------------------------------------------


def test_managers_override_package_name(monkeypatch):
    calls = []

    monkeypatch.setattr(
        pkg_mod.shutil, "which", lambda name: "/usr/local/bin/brew" if name == "brew" else None
    )
    monkeypatch.setattr(pkg_mod.subprocess, "run", lambda cmd, **_: calls.append(cmd))

    events = _run(InstallPackage(name="j", managers={"brew": "autojump"}))

    assert events == [InstallDone("j")]
    assert calls == [["brew", "install", "autojump"]]


# ---------------------------------------------------------------------------
# dry_run — no subprocess, but InstallDone is still yielded
# ---------------------------------------------------------------------------


def test_dry_run_yields_done_no_subprocess(monkeypatch):
    calls = []

    monkeypatch.setattr(
        pkg_mod.shutil, "which", lambda name: "/usr/local/bin/brew" if name == "brew" else None
    )
    monkeypatch.setattr(pkg_mod.subprocess, "run", lambda cmd, **_: calls.append(cmd))

    events = _run(InstallPackage(name="autojump", managers={"brew": "autojump"}), dry_run=True)

    assert events == [InstallDone("autojump")]
    assert calls == []


# ---------------------------------------------------------------------------
# No supported package manager available
# ---------------------------------------------------------------------------


def test_no_pm_found_yields_warning(monkeypatch):
    monkeypatch.setattr(pkg_mod.shutil, "which", lambda _name: None)
    events = _run(InstallPackage(name="autojump", managers={"brew": "autojump"}))
    assert len(events) == 1
    assert isinstance(events[0], Warning)
