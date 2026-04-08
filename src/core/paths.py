from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
HOME = Path.home()


def ppath(path: Path) -> str:
    """Format path for display with ~ for home or repo-root-relative."""
    try:
        return f"~/{path.relative_to(HOME)}"
    except ValueError:
        pass

    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        pass

    return str(path)
