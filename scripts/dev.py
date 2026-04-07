"""setup-dev — install dev tooling (pre-commit hooks) for this repo."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def main() -> None:
    print("→ Installing pre-commit hooks")
    subprocess.run(["uv", "run", "pre-commit", "install", "-f"], check=True, cwd=REPO_ROOT)
    print("  ✓ Done — hooks will run on every commit")


if __name__ == "__main__":
    sys.exit(main())
