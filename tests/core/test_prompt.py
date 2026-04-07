"""Tests for src/core/prompt.py"""

from __future__ import annotations

from src.core.prompt import ask_overwrite


def test_ask_overwrite_enter_returns_true(monkeypatch, tmp_path):
    monkeypatch.setattr("builtins.input", lambda _: "")
    assert ask_overwrite(tmp_path / "file") is True


def test_ask_overwrite_y_returns_true(monkeypatch, tmp_path):
    monkeypatch.setattr("builtins.input", lambda _: "Y")
    assert ask_overwrite(tmp_path / "file") is True


def test_ask_overwrite_n_returns_false(monkeypatch, tmp_path):
    monkeypatch.setattr("builtins.input", lambda _: "n")
    assert ask_overwrite(tmp_path / "file") is False


def test_ask_overwrite_eoferror_returns_false(monkeypatch, tmp_path):
    def raise_eof(_):
        raise EOFError

    monkeypatch.setattr("builtins.input", raise_eof)
    assert ask_overwrite(tmp_path / "file") is False
