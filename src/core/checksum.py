from __future__ import annotations

import hashlib
from pathlib import Path


def checksum(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()
