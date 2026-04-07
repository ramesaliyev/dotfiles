"""Tests for src/core/checksum.py"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from src.core.checksum import checksum, now_iso


def test_checksum_deterministic(tmp_path):
    f = tmp_path / "file.txt"
    f.write_bytes(b"hello world")
    assert checksum(f) == checksum(f)


def test_checksum_differs_for_different_content(tmp_path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_bytes(b"hello")
    b.write_bytes(b"world")
    assert checksum(a) != checksum(b)


def test_checksum_is_sha256(tmp_path):
    f = tmp_path / "file.txt"
    content = b"test content"
    f.write_bytes(content)
    assert checksum(f) == hashlib.sha256(content).hexdigest()


def test_now_iso_is_utc_iso_string():
    result = now_iso()
    dt = datetime.fromisoformat(result)
    assert dt.tzinfo is not None
    assert dt.tzinfo == UTC
