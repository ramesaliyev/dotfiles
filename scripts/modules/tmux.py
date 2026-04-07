"""tmux module — file mappings for collect and bootstrap."""

from pathlib import Path

HOME = Path.home()

README_REL = "dotfiles/tmux/README.md"

POST_BOOTSTRAP_NOTE = (
    "Plugins are managed by TPM (not committed to this repo).\n"
    "  • Fresh machine?  Install TPM first, then Ctrl+A I to install plugins.\n"
    "  • New plugins?    Ctrl+A I inside tmux.\n"
    "  • Config changed? Ctrl+A r to reload.\n"
    "  See dotfiles/tmux/README.md for full instructions."
)

# (source_on_machine, repo-relative destination path)
COLLECT_MAPPINGS: list[tuple[Path, str]] = [
    (HOME / ".tmux.conf",                              "dotfiles/tmux/.tmux.conf"),
    (HOME / ".config/tmux-powerline/config.sh",        "dotfiles/tmux/tmux-powerline/config.sh"),
]

# For themes we glob at runtime — handled specially in collect/bootstrap.
COLLECT_THEMES_SRC = HOME / ".config/tmux-powerline/themes"
COLLECT_THEMES_DEST_REL = "dotfiles/tmux/tmux-powerline/themes"

# (repo-relative source path, destination on machine)
BOOTSTRAP_MAPPINGS: list[tuple[str, Path]] = [
    ("dotfiles/tmux/.tmux.conf",                       HOME / ".tmux.conf"),
    ("dotfiles/tmux/tmux-powerline/config.sh",         HOME / ".config/tmux-powerline/config.sh"),
]

# Themes are also handled specially in bootstrap.
BOOTSTRAP_THEMES_SRC_REL = "dotfiles/tmux/tmux-powerline/themes"
BOOTSTRAP_THEMES_DEST = HOME / ".config/tmux-powerline/themes"
