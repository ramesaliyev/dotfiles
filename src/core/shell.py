from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path


def expand_env_vars(s: str) -> tuple[str, list[str]]:
    """Expand $UPPERCASE_VAR references in s, resolving ~ afterward.

    Looks up each variable in os.environ first; falls back to querying the
    user's interactive shell so that variables set (but not exported) in
    .zshrc/.bashrc are still found when running under uv or similar launchers.

    Returns the expanded string and a list of warning messages for any
    variables that could not be resolved.
    """
    warnings: list[str] = []

    def replacer(m: re.Match) -> str:
        var = m.group(1)
        val = os.environ.get(var) or _query_shell_var(var)
        if val is None:
            warnings.append(f"env var ${var} is not set")
            return m.group(0)
        return val

    # Only match uppercase names (POSIX convention for env vars); lowercase
    # identifiers are left as literals rather than treated as variables.
    expanded = re.sub(r"\$([A-Z_][A-Z0-9_]*)", replacer, s)

    if "~" in expanded:
        expanded = str(Path(expanded).expanduser())

    return expanded, warnings


def _query_shell_var(var: str) -> str | None:
    """Ask the user's interactive shell for the value of a variable.

    Catches variables that are set (but not exported) in .zshrc / .bashrc,
    which os.environ misses because uv spawns a non-interactive child process.
    Returns None if the shell reports an empty/unset value or on any error.
    """
    shell = os.environ.get("SHELL", "/bin/zsh")
    try:
        result = subprocess.run(
            [shell, "-i", "-c", f"echo -n ${var}"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        val = result.stdout.strip()
        return val or None
    except OSError, subprocess.SubprocessError:
        return None
